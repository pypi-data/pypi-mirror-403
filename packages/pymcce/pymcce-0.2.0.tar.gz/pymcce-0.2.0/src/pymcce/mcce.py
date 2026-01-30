import os
import datetime
import logging
from importlib import resources
from collections import defaultdict
import copy
from pathlib import Path
from numba import njit
from numba.typed import Dict
from numba import types
import random
import time
from .utils import *
from scipy.spatial.transform import Rotation as R
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

# constants
from .constants import *  # Import all constants
from .utils import *      # Import all utility functions

def default_prm_file(name: str) -> str:
    """Get the path to the default prm file from package resources."""
    return str(resources.files("pymcce.data.prm").joinpath(name))


def default_ftpl_folder() -> str:
    """Get the path to the default ftpl folder from package resources."""
    folder_res = resources.files("pymcce.data").joinpath("ftpl")
    with resources.as_file(folder_res) as folder_path:
        return str(folder_path)
    

def default_rename_file() -> str:
    """Get the path to the default rename file from package resources."""
    return str(resources.files("pymcce.data.prm").joinpath("rename.txt"))

def default_ideal_structures_folder() -> str:
    """Get the path to the default ideal structures folder from package resources."""
    folder_res = resources.files("pymcce.data").joinpath("ideal_structures")
    with resources.as_file(folder_res) as folder_path:
        return str(folder_path)


def is_H(atomname: str) -> bool:
    """Check if an atom name corresponds to a hydrogen atom."""
    # It is an H atom when full 4 chars starts with H, or the first two chars are " H".
    return (len(atomname.strip()) == 4 and atomname[0] == "H") or (atomname[:2] == " H")


def vdw_atoms_to_atoms(atoms_1, atoms_2, r_cut: float = 10.0) -> float:
    """
    Calculate the van der Waals interaction energy between two conformers using Lennard-Jones potential.

    Parameters
    ----------
    conf1 : Conformer
        The first conformer.
    conf2 : Conformer
        The second conformer.
    r_cut : float
        The cutoff distance for the interaction.

    Returns
    -------
    float
        The van der Waals interaction energy between the two conformers.
    """

    coords_conf1 = np.array([atom.xyz for atom in atoms_1])
    coords_conf2 = np.array([atom.xyz for atom in atoms_2])
    radii_conf1 = np.array([atom.r_vdw for atom in atoms_1])
    radii_conf2 = np.array([atom.r_vdw for atom in atoms_2])
    epsilons_conf1 = np.array([atom.e_vdw for atom in atoms_1])
    epsilons_conf2 = np.array([atom.e_vdw for atom in atoms_2])
    n1 = len(atoms_1)
    n2 = len(atoms_2)
    screening = np.ones((n1, n2), dtype=float)

    # map atoms in conf2 to indices for O(1) lookups
    map2 = {atom: idx for idx, atom in enumerate(atoms_2)}
    for i1, atom1 in enumerate(atoms_1):
        # set 1-4 interactions to 0.5 first (will be overridden by 0.0 for 1-2/1-3/self)
        idxs14 = [map2[a] for a in getattr(atom1, "connect14", []) if a in map2]
        if idxs14:
            screening[i1, idxs14] = 0.5

        # same-atom -> 0.0 (works even when conf1 is same object as conf2)
        j = map2.get(atom1)
        if j is not None:
            screening[i1, j] = 0.0

        # set 1-2 and 1-3 interactions to 0.0 (override any 0.5)
        idxs12 = [map2[a] for a in getattr(atom1, "connect12", []) if a in map2]
        if idxs12:
            screening[i1, idxs12] = 0.0
        idxs13 = [map2[a] for a in getattr(atom1, "connect13", []) if a in map2]
        if idxs13:
            screening[i1, idxs13] = 0.0

    vdw_energy = vdw_pairwise(coords_conf1, radii_conf1, epsilons_conf1, 
                                    coords_conf2, radii_conf2, epsilons_conf2, 
                                    r_cut, sf_matrix=screening)

    return vdw_energy

def precalculate_vdw(mcce):
    energies = Dict.empty(key_type=types.UniTuple(types.int64, 2), value_type=types.float64)
    mcce.reset_connect()
    mcce.make_connect12()
    mcce.make_connect13()
    mcce.make_connect14()
    mcce.assign_radii()

    conformers = []   # each conformer is a list of atoms
    backbone_conformer = [] # collect all backbone atoms first as one conformer
    for residue in mcce.protein.residues:
        if len(residue.conformers) > 0 and len(residue.conformers[0].atoms) > 0:
            backbone_conformer.extend(residue.conformers[0].atoms)  # first conformer is backbone
    conformers.append(backbone_conformer)

    # collect all sidechain conformers
    for residue in mcce.protein.residues:
        for conf in residue.conformers[1:]:
            if len(conf.atoms) > 0:
                conformers.append(conf.atoms)
                conf.i = len(conformers) - 1  # assign index
    
    # Calculate pairwise vdw energies - half matrix
    n_confs = len(conformers)
    for i in range(n_confs):
        vdw_0i = vdw_atoms_to_atoms(conformers[0], conformers[i])
        if abs(vdw_0i) > 0.00001:
            energies[i, 0] = vdw_0i
            energies[0, i] = vdw_0i

    for i in range(1, n_confs):
        atoms_i = conformers[i]
        for j in range(i, n_confs):
            atoms_j = conformers[j]
            vdw_ij = vdw_atoms_to_atoms(atoms_i, atoms_j)
            if abs(vdw_ij) > 0.00001:
                energies[(i, j)] = vdw_ij
                energies[(j, i)] = vdw_ij

    return energies

@njit
def vdw_microstate_ir(i_res, micro, vdw_lookup_table):
    """
    Optimized calculation of the vdw energy contribution from residue i_res
    within a microstate. Uses local variables and cached lookup method to
    reduce attribute/tuple allocation overhead in the hot loop.

    The microstate energy of this conformer of selected residue (i_res) includes: 
    - vdw0 (self), 
    - vdw1 (backbone), 
    - vdw_pw (pairwise with other sidechains in microstate).

    The reason to separate i_res is to avoid calculating all pairwise interactions in the microstate. This function
    returns the vdw interaction from i_res only. It is used in rotamer repacking when we only change one residue at a time.
    
    Inputs:
    i_res : int, residue index of the microstate
    microstate : numpy.ndarray of int, conformer indices (stored in conf.i) of the lookup table, for each residue in the microstate
    vdw_lookup_table : Dict, pre-calculated vdw energies between conformer pairs
    """
    i_c = micro[i_res]

    vdw0 = 0.5 * vdw_lookup_table.get((i_c, i_c), 0.0)
    vdw1 = vdw_lookup_table.get((i_c, 0), 0.0)

    vdw_pw = 0.0
    for idx in range(micro.size):
        if idx == i_res:
            continue
        other_conf = micro[idx]
        vdw_pw += vdw_lookup_table.get((i_c, other_conf), 0.0)

    return vdw0 + vdw1 + vdw_pw


class RotateRule:
    def __init__(self):
        """
        A Rotate Rule defines the rotation axis and the affected atoms to be rotated by atom names.
        """
        self.bond = ()           # (atom1, atom2) in this direction
        self.affected_atoms = [] # list of affected atoms to be rotated

    def __repr__(self):
        return f"RotateRule(axis={self.bond}, affected_atoms={self.affected_atoms})"


def swing_a_conformer(conf, rule: RotateRule, angle_deg: float, heavy_atom_only: bool = True):
    """
    Swing a conformer around the rotation axis defined in rule by angle_deg degrees.

    conf is preserved. Returns a new Conformer or None.
    Optimizations:
    - Early exit if there are no affected atoms present (avoid cloning).
    - Work with name lists / sets to minimize repeated dict lookups.
    - Use numpy arrays for coordinate handling as before.
    """
    atoms_by_name_base = {atom.atomname: atom for atom in conf.atoms}
    # Quick checks
    if rule.bond[0] is None:
        return None  # skip free rotate objects

    bond_name2 = rule.bond[1]
    bond_name1 = rule.bond[0]

    bondatom_p2 = atoms_by_name_base.get(bond_name2, None)
    # If bondatom_p2 missing we can't proceed
    if bondatom_p2 is None:
        logging.warning(f"   {conf.parent_residue.resid} {conf.conftype} {bond_name2} not found in conformer atoms.")
        return None

    # Determine which affected atom names exist in this conformer (preserve order)
    present_names = [n for n in rule.affected_atoms if n in atoms_by_name_base]
    if heavy_atom_only:
        # filter out hydrogens by checking element on the base atoms (faster than string tests per-use)
        present_names = [n for n in present_names if atoms_by_name_base[n].element != " H"]

    if not present_names:
        return None  # nothing to swing, avoid clone

    # Find bondatom_p1: either in same conformer or via connect12 of bondatom_p2
    if bond_name1 in atoms_by_name_base:
        bondatom_p1 = atoms_by_name_base[bond_name1]
    else:
        bondatom_p1 = None
        for connected_atom in bondatom_p2.connect12:
            if connected_atom.atomname == bond_name1:
                bondatom_p1 = connected_atom
                break
        if bondatom_p1 is None:
            logging.warning(f"   {conf.parent_residue.resid} {conf.conftype} {bond_name1} not found in CONNECT of {bond_name2}.")
            return None

    # Clone only now that we know we will modify/create a new conformer
    new_conf = conf.clone()
    new_conf.parent_residue = conf.parent_residue
    new_conf.history = conf.history[:2] + "R" + conf.history[3:]

    # Map names in the cloned conformer to atom objects
    atoms_by_name_new = {atom.atomname: atom for atom in new_conf.atoms}
    # Build affected atoms from the cloned conformer in the preserved order
    affected_atoms = [atoms_by_name_new[name] for name in present_names if name in atoms_by_name_new]

    if not affected_atoms:
        return None  # defensive, though we checked earlier

    # Prepare axis and coordinates
    axis_p1 = np.array(bondatom_p1.xyz)
    axis_p2 = np.array(bondatom_p2.xyz)
    affected_coords = np.vstack([np.array(a.xyz) for a in affected_atoms])

    # Perform rotation (swing_atoms expects list/array, keep same interface)
    new_coords = swing_atoms(axis_p1, axis_p2, affected_coords, angle_deg)

    # Assign new coordinates back to cloned atoms
    for atom, new_xyz in zip(affected_atoms, new_coords):
        atom.xyz = (float(new_xyz[0]), float(new_xyz[1]), float(new_xyz[2]))

    return new_conf


class Tpl:
    """
    Tpl class stores parameters from ftpl files.
    To access a parameter, use tpl[key], where key is a tuple of up to 3 strings.
    """
    # Make Tpl a dictionary-like object
    def __init__(self):
        self._db = {}

    def __getitem__(self, key):
        return self._db[key]
    
    def get(self, key, default=None):
        """
        Get the value for the given key. If the key does not exist, return the default value.
        """
        return self._db.get(key, default)

    def __setitem__(self, key, value):
        self._db[key] = value

    def __delitem__(self, key):
        del self._db[key]

    def __contains__(self, key):
        return key in self._db

    def keys(self):
        return self._db.keys()
    
    def values(self):
        return self._db.values()

    def items(self):
        return self._db.items()

    # FTPL keys are tuples containing up to 3 strings.
    # The value type depends on the record type and must be handled individually.
    # Supported value types include:
    # 1. List of strings (e.g., CONFLIST)
    # 2. Floating point numbers (e.g., CHARGE)
    # 3. Custom objects for complex records (e.g., CONNECT)
    class CONNECT_param:
        """
        CONNECT parameter class.
        Example: CONNECT, " N  ", ASPBK: sp2, " ?  ", " CA ", " H  "
        """
        def __init__(self, value_str):
            parts = [p.strip() for p in value_str.split(",") if p.strip()]
            self.orbital = parts[0]
            self.connected = [p.strip('"') for p in parts[1:]]

        def __str__(self):
            connected_str = ", ".join(f'"{atom}"' for atom in self.connected)
            return f"{self.orbital}, {connected_str}"

    class RADIUS_param:
        """
        RADII parameter class
        Example: RADIUS, ASPBK, " N  ": 1.500, 1.824, 0.170
        """
        def __init__(self, value_str):
            fields = value_str.split(",")
            self.r_bound = float(fields[0].strip())
            self.r_vdw = float(fields[1].strip())
            self.e_vdw = float(fields[2].strip())

        def __str__(self):
            return f"{self.r_bound}, {self.r_vdw}, {self.e_vdw}"

    class CONFORMER_param:
        """
        CONFORMER parameter class
        Example: CONFORMER, ASP01: Em0=   0.0, pKa0=  0.00, ne= 0, nH= 0, rxn02= -6.320, rxn04= -2.93, rxn08= -1.38
        """
        def __init__(self, value_str):
            fields = value_str.split(",")
            for f in fields:
                k, v = f.split("=")
                setattr(self, k.strip().lower(), float(v.strip()))

        def __str__(self):
            return ", ".join([f"{k}={v}" for k, v in vars(self).items()])

    class ROTATE_param:
        """
        ROTATE parameter class
        Example: ROTATE, ASP: " CA " - " CB ", " CB " - " CG "
        """
        def __init__(self, value_str):
            fields = value_str.split(",")
            rotatables = [tuple([a.strip().strip('"') for a in f.split("-")]) for f in fields]
            self.rotatables = rotatables

        def __str__(self):
            return ", ".join([f'"{a}" - "{b}"' for a, b in self.rotatables])

    class ROT_SWAP_param:
        """
        ROT_SWAP parameter class
        Example: ROT_SWAP, HIS: " ND1" - " CD2",  " CE1" - " NE2"
        """
        def __init__(self, value_str):
            fields = value_str.split(",")
            swapables = [tuple([a.strip().strip('"') for a in f.split("-")]) for f in fields]
            self.swapables = swapables

        def __str__(self):
            return ", ".join([f'"{a}" - "{b}"' for a, b in self.swapables])
    

    class LIGAND_ID_param:
        """
        LIGAND_ID parameter class
        Examples:
        LIGAND_ID, CYS, CYS: " SG " - " SG "; 2.00 +- 0.20; CYL, CYL
        LIGAND_ID, HIS, HEM: " NE2" - "FE  "; 2.50 +- 0.25; HIL, HEM
        LIGAND_ID, HIS, HEA: " NE2" - "FE  "; 2.50 +- 0.25; HIL, HEA
        LIGAND_ID, HIS, HEB: " NE2" - "FE  "; 2.50 +- 0.25; HIL, HEB
        LIGAND_ID, HIS, HEC: " NE2" - "FE  "; 2.50 +- 0.25; HIL, HEC
        LIGAND_ID, MET, HEA: " SD " - "FE  "; 2.50 +- 0.25; HIL, HEA
        LIGAND_ID, MET, HEB: " SD " - "FE  "; 2.50 +- 0.25; HIL, HEB
        LIGAND_ID, MET, HEC: " SD " - "FE  "; 2.50 +- 0.25; HIL, HEC
        """
        def __init__(self, value_str):
            fields = value_str.split(";")
            # atom pair
            atom1, atom2 = fields[0].strip().split("-")
            self.atom1 = atom1.strip().strip('"')
            self.atom2 = atom2.strip().strip('"')
            # ligand bond distance and tolerance
            distance, tolerance = fields[1].strip().split("+-")
            self.distance = float(distance.strip())
            self.tolerance = float(tolerance.strip())
            # residue rename to
            name1, name2 = fields[2].strip().split(",")
            self.res1_name = name1.strip()
            self.res2_name = name2.strip()  

        def __str__(self):
            value_str = f'"{self.atom1}" - "{self.atom2}"; {self.distance} +- {self.tolerance}; {self.res1_name}, {self.res2_name}'
            return value_str


    # Tpl class methods               
    def load_ftpl_file(self, file):
        """
        Load a ftpl file.
        Sample ftpl file:
        ---------------------------------------
        # Values of the same key are appended and separated by ","
        CONFLIST, ASP: ASPBK, ASP01, ASP02, ASP-1

        # Atom definition
        CONNECT, " N  ", ASPBK: sp2, " ?  ", " CA ", " H  "
        CONNECT, " H  ", ASPBK: s, " N  "
        CONNECT, " CA ", ASPBK: sp3, " N  ", " C  ", " CB ", " HA "
        CONNECT, " HA ", ASPBK: s, " CA "
        CONNECT, " C  ", ASPBK: sp2, " CA ", " O  ", " ?  "
        ---------------------------------------
        : separates key and value
        The key is the fields (up to 3) before the first : in a line.
        The value is the fields after the first : in a line.
        """

        with open(file) as f:
            for line in f:
                entry_str = line.split("#")[0].strip()
                fields = entry_str.split(":")
                if len(fields) == 2:
                    key_str = fields[0].strip()
                    # we have up to 3 keys, separated by ","
                    keys = key_str.split(",")
                    key1 = keys[0].strip().strip('"')
                    key2 = keys[1].strip().strip('"') if len(keys) > 1 else ""
                    key3 = keys[2].strip().strip('"') if len(keys) > 2 else ""
                    
                    value_str = fields[1].strip()
                    warn_duplicate_msg = "   Duplicate key {}. Overwriting its value ..."

                    # We have to handle the value case by case here, once for all.
                    if key1 == "CONFLIST":  # value stored as a list of strings
                        key = (key1, key2)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = [v.strip() for v in value_str.split(",")]
                    elif key1 == "CONNECT":  # value stored as a complex object
                        key = (key1, key2, key3)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = self.CONNECT_param(value_str)
                    elif key1 == "RADIUS":
                        key = (key1, key2, key3)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = self.RADIUS_param(value_str)
                    elif key1 == "CONFORMER":
                        key = (key1, key2)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = self.CONFORMER_param(value_str)
                    elif key1 == "CHARGE":  # value stored as a float point number
                        key = (key1, key2, key3)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = float(value_str)
                    elif key1 == "ROTATE":
                        key = (key1, key2)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = self.ROTATE_param(value_str)
                    elif key1 == "ROT_SWAP":
                        key = (key1, key2)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = self.ROT_SWAP_param(value_str)
                    elif key1 == "TORSION":
                        logging.debug(f"   TORSION parameters are not used in this version of MCCE.")
                    elif key1 == "LIGAND_ID":
                        key = (key1, key2, key3)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = self.LIGAND_ID_param(value_str)
                    elif key1 == "EXTRA" or key1 == "SCALING":  # captures 2-key float value type parameters
                        key = (key1, key2)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = float(value_str)
                    elif key1 == "LOOSE" and key2 == "COFACTORS":
                        key = (key1, key2)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = [v.strip().strip('"') for v in value_str.split(",") if v.strip()]
                    else:
                        logging.warning(f"   {key1} parameters are not defined in Tpl, value treated as string.")
                        key = (key1, key2, key3)
                        if key in self:
                            logging.warning(warn_duplicate_msg.format(key))
                        self[key] = value_str

            logging.debug(f"   Loaded ftpl file {file}")
    


    def dump(self, file_path=FTPL_DUMP, comment=""):
        """
        Dump the parameters in the format of a tpl file.
        """
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(file_path, "w") as f:
            f.write(f"# This tpl file is recorded on {date}\n{comment}\n")
            for key, value in self.items():
                # wrap double quotes if a key has leading or ending spaces, and are 4 characters long
                key_str = ", ".join(f'"{k}"' if len(k) == 4 and (k[0] == " " or k[-1] == " ") else k for k in key)
                if isinstance(value, list):
                    # wrap double quotes if a list item has leading or ending spaces
                    value_str = ", ".join(f'"{v}"' if v.startswith(" ") or v.endswith(" ") else v for v in value)
                else:
                    value_str = str(value)
                line = "%s: %s\n" % (key_str, value_str)
                f.write(line)

class ROT_STAT_item:
    def __init__(self) -> None:
        """Rotamer making recording structure for each residue"""
        self.start = 0       # conformer count at the start
        self.swap = 0        # conformer count after swap
        self.rotate = 0      # conformer count after heavy atom rotamer
        self.clean = 0       # conformer count after self energy cleaning
        self.hbond = 0       # conformer count after hydrogen bond directed rotamer making
        self.repack = 0      # conformer count after repacking, GA repacking included
        self.xposed = 0      # conformer count after adding the most exposed conformer
        self.ioni = 0        # conformer count after ionization conformers are made, proton added in this step
        self.torh = 0        # conformer count after torsion minimum H is created
        self.oh = 0          # conformer count after H bond hydrogen is created
        self.cluster = 0     # conformer count after clustering and election are made (limit conformer to <= 999)

    def __repr__(self):
        return (f"ROT_STAT_item(start={self.start}, swap={self.swap}, rotate={self.rotate}, "
                f"clean={self.clean}, hbond={self.hbond}, repack={self.repack}, "
                f"xposed={self.xposed}, ioni={self.ioni}, torh={self.torh}, "
                f"oh={self.oh}, cluster={self.cluster})")


def make_rotate_rules(tpl: Tpl) -> dict[str, list['RotateRule']]:
    """
    Use ROTATE and CONNECT records in tpl to make RotateRule objects for conformers.

    Parameters
    ----------
    tpl : Tpl
        The topology object containing ROTATE and CONNECT records.

    Returns
    -------
    dict[str, list[RotateRule]]
        A dictionary indexed by conftype with lists of RotateRule objects as values.
    """
    # This is the dictionary that will be returned at the end.
    rotate_rules = defaultdict(list)

    # Make rotate rules from ftpl
    for key, value in tpl.items():
        if key[0] == "ROTATE":
            resname = key[1]
            rotatble_bonds = value.rotatables
            conftypes = tpl[("CONFLIST", resname)]
            # search affected atoms of the side chain confs only
            for conftype in conftypes:
                if conftype[-2:] == "BK":  # backbone conformers don't rotate
                    continue
                for bond in rotatble_bonds:
                    rule = RotateRule()
                    rule.bond = bond
                    query_key = ("CONNECT", bond[1], conftype)  # look for connected atoms of atom2 in the bond
                    if query_key in tpl:
                        rule.affected_atoms.extend([
                            a for a in tpl[query_key].connected
                            if a not in bond and ("?" not in a)
                        ])  # affected atoms exclude the bond atoms and unknown atoms
                        # continue to extend the affected atom list by looking for connected atoms of affected atoms
                        for atom in rule.affected_atoms:  # rule.affected_atoms will be extended in the loop
                            query_key = ("CONNECT", atom, conftype)
                            if query_key in tpl:
                                rule.affected_atoms.extend([
                                    a for a in tpl[query_key].connected
                                    if (a not in rule.affected_atoms)
                                    and (a not in bond)
                                    and ("?" not in a)
                                ])
                        rotate_rules[conftype].append(rule)
                    else:
                        logging.warning(f"   {resname} {conftype} {bond} not found in CONNECT")
    
    # Make rotate rules from H atom rotation freedom test, as H atoms are not included in ROTATE records
    for key, value in tpl.items():
        if key[0] == "CONNECT" and key[2][-2:] != "BK":  # only side chain confs
            atomname = key[1]
            conftype = key[2]
            if is_H(atomname):  # find H, then find the bonded heavy atom
                atom = None
                orbital = None
                connected_hvatoms = []
                for candidate_atom in value.connected:  # this should be the only heavy atom connected to the H
                    if not is_H(candidate_atom):
                        atom = candidate_atom
                        query_key = ("CONNECT", atom, conftype)
                        orbital = tpl[query_key].orbital
                        connected_hvatoms = [a for a in tpl[query_key].connected if not is_H(a)]
                        break
                # print(f"   {atomname} {conftype} {atom}: {orbital} {connected_hvatoms}")
                if atom is not None and orbital is not None:
                    if orbital == "sp3" and len(connected_hvatoms) == 1:  # rotatable oribital and bond has freedom
                        rule = RotateRule()
                        rule.bond = (connected_hvatoms[0], atom)  # bond is defined as (atom1, atom2)
                        query_key = ("CONNECT", atom, conftype)
                        if query_key in tpl:
                            rule.affected_atoms.extend([a for a in tpl[query_key].connected if a not in rule.bond])  # should all be H atoms
                            rotate_rules[conftype].append(rule)
                    elif orbital == "sp3" and len(connected_hvatoms) == 0:  # free rotatable orbital, e.g., HOH, NH4+
                        rule = RotateRule()
                        rule.bond = (None, atom)  # this is a special case to account for free rotate objects like HOH and NH4+
                        query_key = ("CONNECT", atom, conftype)
                        if query_key in tpl:
                            rule.affected_atoms.extend([a for a in tpl[query_key].connected if a not in rule.bond])  # should all be H atoms
                            # print(f"   Free rotate object {conftype} {atom}: Affected atoms {rule.affected_atoms}")
                            rotate_rules[conftype].append(rule)

    # Clean up the duplicates in the rotate rules defined by rotatable bonds
    for key, value in rotate_rules.items():
        recorded_bonds = []
        clean_rules = []
        for rule in value:
            if rule.bond not in recorded_bonds:
                recorded_bonds.append(rule.bond)
                clean_rules.append(rule)
        rotate_rules[key] = clean_rules

    return rotate_rules


def create_h(center_atom, h_name, h_pos):
    """
    Create a hydrogen atom object.

    Parameters
    ----------
    center_atom : Atom
        The heavy atom to which the hydrogen is bonded.
    h_name : str
        The name of the hydrogen atom.
    h_pos : tuple of float
        The (x, y, z) coordinates of the hydrogen atom.

    Returns
    -------
    Atom
        The created hydrogen atom object.
    """
    h_atom = Atom()
    h_atom.record = center_atom.record
    h_atom.atomname = h_name
    h_atom.altloc = center_atom.altloc
    h_atom.resname = center_atom.resname
    h_atom.chain = center_atom.chain
    h_atom.sequence = center_atom.sequence
    h_atom.insertion = center_atom.insertion
    h_atom.xyz = h_pos
    h_atom.element = " H"
    h_atom.parent_conformer = center_atom.parent_conformer
    h_atom.connect12 = [center_atom]
    return h_atom

def place_hydrogens_sp3(atom=None, connected_heavy_atoms=[], missing_h_names=[], connect_param=None):
    v0 = np.array(atom.xyz)
    n_known = len(connected_heavy_atoms)
    
    # Determine H positions based on number of known connected atoms
    if n_known == 3:
        v1, v2, v3 = [np.array(a.xyz) for a in connected_heavy_atoms]
        h_positions = list(sp3_3known(v0, v1, v2, v3))
    elif n_known == 2:
        v1, v2 = [np.array(a.xyz) for a in connected_heavy_atoms]
        h_positions = list(sp3_2known(v0, v1, v2))
    elif n_known == 1:
        v1 = np.array(connected_heavy_atoms[0].xyz)
        h_positions = list(sp3_1known(v0, v1))
    else:  # n_known == 0
        h_positions = list(sp3_0known(v0))
    
    # Create H atoms for each missing H name, using available positions
    for h_name in missing_h_names:
        if h_positions:
            h_pos = h_positions.pop(0)
            h_atom = create_h(atom, h_name, h_pos)
            atom.parent_conformer.atoms.append(h_atom)


def place_hydrogens_sp2(atom=None, connected_heavy_atoms=[], missing_h_names=[], connect_param=None):
    v0 = np.array(atom.xyz)
    n_known = len(connected_heavy_atoms)
    
    # Determine H positions based on number of known connected atoms
    h_positions = []  # initialize empty list
    if n_known == 2:
        v1, v2 = [np.array(a.xyz) for a in connected_heavy_atoms]
        h_positions = list(sp2_2known(v0, v1, v2))
    elif n_known == 1:
        known_heavy_atom = connected_heavy_atoms[0]
        v1 = np.array(known_heavy_atom.xyz)
        # find the heaviest atom connected to the known heavy atom
        heaviest_atom = None
        max_atom_mass = 0.0
        for connected_atom in known_heavy_atom.connect12:
            atom_mass = ATOM_MASSES[connected_atom.element]
            if connected_atom.element != " H" and connected_atom != atom and atom_mass > max_atom_mass:
                heaviest_atom = connected_atom
                max_atom_mass = atom_mass
        if heaviest_atom is not None:
            v1e = np.array(heaviest_atom.xyz)
        else:
            v1e = None
        h_positions = list(sp2_1known(v0, v1, v1e))            
    else:  # n_known == 0
        h_positions = list(sp2_0known(v0))

    # Create H atoms for each missing H name, using available positions
    for h_name in missing_h_names:
        if h_positions:
            h_pos = h_positions.pop(0)
            h_atom = create_h(atom, h_name, h_pos)
            atom.parent_conformer.atoms.append(h_atom)


def place_hydrogens_sp(atom=None, connected_heavy_atoms=[], missing_h_names=[], connect_param=None):
    # Place hydrogen on the opposite side of the known heavy atom
    v0 = np.array(atom.xyz)
    n_known = len(connected_heavy_atoms)
    h_positions = []  # initialize empty list
    if n_known == 1:
        v1 = np.array(connected_heavy_atoms[0].xyz)
        h_positions = list(sp_1known(v0, v1))
    else:  # n_known == 0
        logging.warning(f"   SP orbital with 0 known connected atoms is not supported. Skipping H placement for atom {atom.atomname} in {atom.get_confid()}.")

    # Create H atoms for each missing H name, using available positions
    for h_name in missing_h_names:
        if h_positions:
            h_pos = h_positions.pop(0)
            h_atom = create_h(atom, h_name, h_pos)
            atom.parent_conformer.atoms.append(h_atom)

class Atom:
    """
    Atom class
    """
    def __init__(self):
        # Attributes defined by PDB file
        self.record = ""            # Record name ("ATOM" or "HETATM")
        self.serial = 0             # Atom serial number
        self.atomname = ""          # Atom name
        self.altloc = ""            # Alternate location indicator
        self.resname = ""           # Residue name
        self.chain = ""             # Chain ID
        self.sequence = 0           # Residue sequence number
        self.insertion = ""         # Insertion code
        self.xyz = (0.0, 0.0, 0.0)  # Coordinates (x, y, z)
        # Extended attributes
        self.charge = 0.0           # Charge
        self.r_boundary = 0.0       # Boundary radius
        self.r_vdw = 0.0            # van der Waals radius
        self.e_vdw = 0.0            # van der Waals energy well depth
        self.element = ""           # Element name
        self.connect12 = []         # List of atoms 1-2 bonded
        self.connect13 = []         # List of atoms 1-3 bonded
        self.connect14 = []         # List of atoms 1-4 bonded
        self.parent_conformer = None     # Parent conformer

    def load_pdbline(self, line):
        """
        Load atom attributes from a PDB line.
        """
        self.record    = line[0:6]
        self.atomname  = line[12:16]
        self.altloc    = line[16]
        self.resname   = line[17:20]
        self.chain     = line[21]
        self.sequence  = int(line[22:26])
        self.insertion = line[26] if line[26] != " " else "_"
        self.xyz       = (
            float(line[30:38]),
            float(line[38:46]),
            float(line[46:54])
        )
        atomname_stripped = self.atomname.strip()
        if len(atomname_stripped) == 4 and atomname_stripped.startswith("H"):
            self.element = " H"
        else:
            self.element = self.atomname[:2]


    def load_mcceline(self, line):
        """
        Load the atom from a MCCE PDB line.
        """
        self.record     = line[0:6]
        self.atomname   = line[12:16]
        self.altloc     = line[16]
        self.resname    = line[17:20]
        self.chain      = line[21]
        self.sequence   = int(line[22:26])
        self.insertion  = line[26] if line[26] != " " else "_"
        self.confnum    = int(line[27:30])
        self.xyz        = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
        self.r_boundary = float(line[54:62])
        self.charge     = float(line[62:74])
        self.history    = line[80:90]

        # Determine element
        atomname_stripped = self.atomname.strip()
        self.element = " H" if len(atomname_stripped) == 4 and atomname_stripped.startswith("H") else self.atomname[:2]
        self.parent_conformer = None  # to be set when the conformer is created

    def get_confid(self):
        """
        Return the MCCE conformer ID.
        Example: "ASP01A000_000", "GLN01A0121_001"
        """
        return f"{self.resname}{self.history[:2]}{self.chain}{self.sequence:04d}{self.insertion}{self.confnum:03d}"

    def get_resid(self):
        """
        Return the residue ID.
        """
        return (self.resname, self.chain, self.sequence, self.insertion)
    

    def as_mccepdb_line(self):
        """
        Return the atom as a pdb line.
        """
        serial = self.serial % 100000        
        return "%-6s%5d %4s %3s %c%04d%c%03d%8.3f%8.3f%8.3f%8.3f%12.3f      %s\n" % (
            self.record,
            serial,
            self.atomname,
            self.parent_conformer.parent_residue.resname,
            self.parent_conformer.parent_residue.chain,
            self.parent_conformer.parent_residue.sequence,
            self.parent_conformer.parent_residue.insertion,
            self.parent_conformer.confnum,
            self.xyz[0],
            self.xyz[1],
            self.xyz[2],
            self.r_boundary,
            self.charge,
            self.parent_conformer.history
        )

    def clone(self):
        """
        Return a customized copy (between shallow and deep copy) of the atom.
        """
        new_atom = copy.copy(self)
        new_atom.connect12 = []
        new_atom.connect13 = []
        new_atom.connect14 = []
        return new_atom

class Conformer:
    """
    Conformer class
    """
    def __init__(self):
        self.confid = ""            # conformer name, unique ID in the protein. resname+conftype+chain+sequence+insertion+confnum
        self.conftype = ""          # conformer type, as defined in CONFLIST without residue name in the ftpl file
        self.confnum = 0            # conformer number
        self.history = ""           # history string
        self.charge = 0.0           # net charge
        self.atoms = []             # list of atoms in the conformer
        self.parent_residue = None  # parent residue

    def clone(self):
        """
        Return a customized copy (between shallow and deep copy) of the conformer.
        """
        new_conformer = copy.copy(self)
        new_conformer.atoms = [atom.clone() for atom in self.atoms]
        for atom in new_conformer.atoms:
            atom.parent_conformer = new_conformer

        # Repair connect12 references to point to new atoms within the new conformer
        old_atoms = self.atoms
        new_atoms = new_conformer.atoms
        mapping = {old: new for old, new in zip(old_atoms, new_atoms)}
        mg = mapping.get
        for old, new in zip(old_atoms, new_atoms):
            new.connect12 = [mg(a, a) for a in old.connect12]
            new.connect13 = [mg(a, a) for a in getattr(old, 'connect13', [])]
            new.connect14 = [mg(a, a) for a in getattr(old, 'connect14', [])]

        return new_conformer


class Residue:
    """
    Residue class
    """
    def __init__(self):
        self.resname = ""           # residue name
        self.chain = ""             # chain ID
        self.sequence = 0           # residue sequence number
        self.insertion = ""         # insertion code
        self.conformers = []        # list of conformers in the residue
        self.resid = ""             # residue ID, resname+chain+sequence+insertion


class Protein:
    """
    Protein class to store protein structure information.
    This is a hierarchical structure:
    Protein -> Residues -> Conformers -> Atoms
    """
    def __init__(self):
        self.residues = []  # list of Residue objects

    def serialize(self):
        # serialize the protein:
        # 1. atom serial number
        # 2. conformer number
        # 3. conformer ID
        # 4. conformer history (same heavy atom type counts in a serials, H atom type counts in regard to heavy and H types)
        atom_counter = 0
        for res in self.residues:
            for conf_counter, conf in enumerate(res.conformers):
                conf.confnum = conf_counter
                conf.confid = f"{res.resname}{conf.conftype}{res.chain}{res.sequence:04d}{res.insertion}{conf.confnum:03d}"
                for atom in conf.atoms:
                    atom_counter += 1
                    atom.serial = atom_counter
        # history string is tricky, as it carries information about how the conformer is inherited from the parent
        # Sample history string: "BKO000_000" or "01R000M000"
        # history[:2] is the conformer type,
        # history[2] is rotamer type
        # history[3:6] rotamer number of that type
        # history[6] is how H atom is placed
        # history[7:10] is the conformer number of H atom placement of the type
        for res in self.residues:
            counter_heavy_type = defaultdict(int)
            for conf in res.conformers:
                heavy_confType = conf.history[:6]
                conf.history = f"{conf.history[:3]}{counter_heavy_type[heavy_confType]:03d}{conf.history[6:]}"
                counter_heavy_type[heavy_confType] += 1

            # renumber H atom history
            heavy_id = defaultdict(int)
            for conf in res.conformers:
                id = conf.history[:7]
                conf.history = f"{id}{heavy_id[id]:03d}"
                heavy_id[id] += 1

    def dump_lines(self):
        """
        Dump the protein as a list of pdb lines.
        """
        self.serialize()
        lines = []
        for res in self.residues:
            lines.append("#" + "=" * 89 + "\n")
            lines.append(f"# Residue: {res.resname} {res.chain}{res.sequence:4d}{' ' if res.insertion == '_' else res.insertion}\n")
            lines.append("#" + "=" * 89 + "\n")
            for conf in res.conformers:
                lines.append(f"## Conformer ID={conf.confid} History={conf.history}\n")
                lines.extend(atom.as_mccepdb_line() for atom in conf.atoms)
                lines.append("#" + "-" * 89 + "\n")
        return lines

class MCCE:
    def __init__(self, prm: str = None, ftpl: str = None):
        """
        MCCE class to handle MCCE data structures and operations.
        These are the three main attributes of MCCE class:
        1. self.prm: dictionary to store run parameters from prm file and command line options.
        2. self.tpl: Tpl object to store parameters from ftpl files.
        3. self.protein: Protein object to store the hierarchical structure of the protein.
        """
        self.default_prm = "run.prm.default"
        self.prm_file = prm if prm else default_prm_file(self.default_prm)
        self.prm = {}
        self.ftpl_folder = ftpl if ftpl else default_ftpl_folder()
        self.tpl = Tpl()
        self.rename_rules = []  # list of (from, to) tuples
        self.ideal_structures_folder = default_ideal_structures_folder()
        self.pdblines = []
        self.protein = None     # Placeholder for hierarchical protein object
        self.link_lines = []    # List of LINK and SSBOND lines generated during ligand detection
        # Load prm and ftpl files during initialization
        self.load_prm_file(self.prm_file)       # this updates self.prm
        self.load_ftpl_files(self.ftpl_folder)  # this updates self.tpl


    def load_prm_file(self, prm: str):
        """Load parameters from the specified prm file.
        Note: The defaulting logic for the prm file is handled in __init__, so this method expects a valid file path.
        """
        logging.info(f"Loading prm file from {self.prm_file}")

        try:
            with open(prm, 'r') as f:
                for line in f:
                    line = line.split('#', 1)[0].strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2 and parts[-1].startswith('(') and parts[-1].endswith(')'):
                        key = parts[-1][1:-1].strip()
                        value = parts[0].strip()
                        self.prm[key] = value
        except (FileNotFoundError, PermissionError, OSError) as e:
            logging.error(f"Failed to open prm file '{prm}': {e}")
            exit(1)
            

    def dump_prm(self, fname: str):
        """Dump the current parameters to a file."""
        with open(fname, 'w') as f:
            f.write(f"# Run parameters used by pymcce. Loaded from {self.prm_file}, modified by command line options.\n")
            for key, value in self.prm.items():
                f.write(f"{value} ({key})\n")

    def load_rename_rules(self, rename: str):
        """Load renaming rules from a file. If no file is provided, use the default rename file."""
        STR_LENGTH = 14
        SEP_LENGTH = 2
        self.rename_rules = []
        if not rename:
            rename = default_rename_file()
        try:
            with open(rename, 'r') as f:
                for line in f:
                    line = line.split('#', 1)[0]
                    if len(line) < 2 * STR_LENGTH + SEP_LENGTH:
                        continue
                    str_from = line[:STR_LENGTH]
                    str_to = line[STR_LENGTH + SEP_LENGTH : 2 * STR_LENGTH + SEP_LENGTH]
                    self.rename_rules.append((str_from, str_to))
        except (FileNotFoundError, PermissionError, OSError) as e:
            logging.error(f"Failed to open rename file '{rename}': {e}")
            exit(1)
        logging.info(f"Loaded {len(self.rename_rules)} renaming rules from {rename}")


    def load_ftpl_files(self, ftpl: str):
        """Load all ftpl files from the specified folder. This function is used during initialization, and also can be called later to load additional ftpl files."""
        logging.info(f"Loading ftpl files from {ftpl}")
        for filename in os.listdir(ftpl):
            if filename.endswith('.ftpl'):
                self.tpl.load_ftpl_file(os.path.join(ftpl, filename))
                logging.debug(f"Loading ftpl file: {filename}")

    def read_plainpdb(self, input_file: str):
        """Read a PDB file and filter relevant lines. Checks for multiple models and altLocs on backbone atoms."""
        with open(input_file, 'r') as f:
            self.pdblines = [
                line for line in f
                if line.startswith(('ATOM  ', 'HETATM', 'MODEL ', 'ENDMDL'))
            ]
        logging.info(f"Read {len(self.pdblines)} lines from PDB file {input_file}")

        # Check for multiple models
        model_count = sum(1 for line in self.pdblines if line.startswith('MODEL '))
        if model_count > 0:
            logging.error(f"Detected {model_count} models in the PDB file. Use pdbtools to split them if needed.")
            exit(1)

        # Check for altLocs on backbone atoms
        altloc_backbone = set("A") # 'A' is the default altLoc in PDB
        report_theselines = []
        for line in self.pdblines:
            if len(line) < 17:
                continue
            atom_name = line[12:16]
            altloc = line[16]
            res_name = line[17:20]
            if atom_name in BACKBONE_ATOMS and res_name in RESIDUE_NAMES and altloc not in (' ', 'A'):
                altloc_backbone.add(altloc)
                report_theselines.append(line)
        if len(altloc_backbone) > 1:
            logging.error(
                f"AltLocs on backbone: {sorted(altloc_backbone)}. "
                "Use pdbtools to resolve them before proceeding:"
            )
            for l in report_theselines:
                print(l.rstrip())
            exit(1)

    def rename_pdb(self):
        """
        Rename residues in the PDB lines based on the loaded renaming rules.
        '*' matches any character. The first string is to match, the second string is the replacement.
        The renaming is accumulative, i.e., a line can be renamed multiple times in the order specified by the rules.
        The matched part of PDB line is [12:26], which includes atom name, altLoc, residue name, chain ID, and residue sequence number.
        
        Sample PDB lines:
        ATOM   1666  HA  GLU A 104     -14.693   6.334  -6.576  1.00  0.00           H
        ATOM   1667  HB2 GLU A 104     -15.958   4.930  -8.912  1.00  0.00           H
        ATOM   1668  HB3 GLU A 104     -16.869   6.197  -8.106  1.00  0.00           H
        ATOM   1669  HG2 GLU A 104     -14.006   6.656  -9.002  1.00  0.00           H
        ATOM   1670  HG3 GLU A 104     -15.414   6.960 -10.033  1.00  0.00           H
        TER    1671      GLU A 104                                                  
        HETATM 1672 FE   HEC A 105       4.144   0.732  -0.600  1.00  0.00          FE
        HETATM 1673  CHA HEC A 105       3.972  -2.562  -1.643  1.00  0.00           C
        HETATM 1674  CHB HEC A 105       0.783   0.698   0.074  1.00  0.00           C
        HETATM 1675  CHC HEC A 105       4.605   3.628   1.038  1.00  0.00           C
        HETATM 1676  CHD HEC A 105       7.433   0.840  -1.776  1.00  0.00           C
        HETATM 1677  NA  HEC A 105       2.668  -0.698  -0.690  1.00  0.00           N
        HETATM 1678  C1A HEC A 105       2.840  -1.961  -1.141  1.00  0.00           C
        HETATM 1679  C2A HEC A 105       1.570  -2.618  -1.121  1.00  0.00           C
        HETATM 1680  C3A HEC A 105       0.644  -1.715  -0.655  1.00  0.00           C
        
        Sample rules:
        ***** ********  *****_********
        ****** *******  ******_*******
        ******* ******  *******_******
        D***** ******   H*****_******
        D************   H************
        DD***** ******  HD*****_******
        DD************  HD************
        DE***** ******  HE*****_******
        DE************  HE************
        *****HEA******  *****HEM******
        *****HEC******  *****HEM******
        *CAA*HEM******  *****PAA******      extract propionate PAA from heme
        *CBA*HEM******  *****PAA******
        *CGA*HEM******  *****PAA******
        *O1A*HEM******  *****PAA******
        *O2A*HEM******  *****PAA******
        HAA**HEM******  *****PAA******
        HBA**HEM******  *****PAA******
        *H1A*HEM******  *****PAA******
        *H2A*HEM******  *****PAA******

        """
        def match_rule2string(rule, string):
            return all(r == "*" or r == s for r, s in zip(rule, string))

        def rename_rule2string(rule, string):
            return "".join([r if r != "*" else s for r, s in zip(rule, string)])        
        
        if not self.rename_rules:
            logging.info("No rename rules loaded, skipping renaming step.")
            return

        renamed_line_count = 0
        renamed_count = 0
        new_pdblines = []
        for line in self.pdblines:
            renamed = False
            string_to_check = line[12:26]
            for str_from, str_to in self.rename_rules:
                if match_rule2string(str_from, string_to_check):
                    new_str = rename_rule2string(str_to, string_to_check)
                    line = line[:12] + new_str + line[26:]
                    renamed_count += 1
                    renamed = True
                    string_to_check = line[12:26]  # update for further matching
            new_pdblines.append(line)
            if renamed:
                renamed_line_count += 1
        self.pdblines = new_pdblines
        logging.info(f"Renamed {renamed_line_count} lines and applied renaming rules {renamed_count} times.")

    def pdblines2atoms(self):
        """Convert the PDB lines to an internal atom representation."""
        atoms = []
        for line in self.pdblines:
            atom = Atom()
            atom.load_pdbline(line)
            if atom.element != " H":  # Skip hydrogen atoms as MCCE will recreate them anyway
                atoms.append(atom)
        self.atoms = atoms

    def remove_waters(self):
        """Remove water molecules from the atom list."""
        original_count = len(self.atoms)
        self.atoms = [atom for atom in self.atoms if atom.resname != "HOH"]
        removed_count = original_count - len(self.atoms)
        logging.info(f"Removed {removed_count} water molecules.")

    def strip_exposed_cofactors(self, sas_cutoff):
        """Strip exposed cofactors based on SAS cutoff. sas_cutoff is in percentage (0-1) at residue level."""
        sas_cutoff = float(sas_cutoff)  # ensure it's a float
        removed_count = 1  # Initialize to enter the loop
        strip_tries = 0
        while removed_count > 0:
            removed_count = 0   
            strip_tries += 1
            # Calculate SAS for each atom, again
            coordinates = np.array([atom.xyz for atom in self.atoms])
            radii = np.array([ATOM_RADII.get(atom.element, ATOM_RADIUS_UNKNOWN) for atom in self.atoms])
            atom_sas = sas(coordinates, radii)
            for i, atom in enumerate(self.atoms):
                atom.sas = atom_sas[i]
                atom.r_boundary = radii[i]

            # Group atoms by residue
            residue_atoms = defaultdict(list)
            for atom in self.atoms:
                residue_atoms[atom.get_resid()].append(atom)

            # Calculate SAS for each residue
            residue_sas = {}
            for resid, residue_atoms in residue_atoms.items():
                inprotein_sas = sum(atom.sas * 4 * np.pi * (atom.r_boundary + SAS_PROBE_RADIUS)**2 for atom in residue_atoms)
                resatom_coordinates = np.array([atom.xyz for atom in residue_atoms])
                res_atom_radii = np.array([atom.r_boundary for atom in residue_atoms])
                atom_sas = sas(resatom_coordinates, res_atom_radii)
                resatom_naked_sas = sum(atom_sas[i] * 4 * np.pi * (res_atom_radii[i] + SAS_PROBE_RADIUS)**2 for i in range(len(residue_atoms)))
                residue_sas[resid] = inprotein_sas / resatom_naked_sas if resatom_naked_sas > 0 else 0.0

            # Remove residues with SAS above cutoff and in loose cofactor list
            original_count = len(self.atoms)
            self.atoms = [atom for atom in self.atoms if residue_sas[atom.get_resid()] <= sas_cutoff or atom.resname not in self.tpl.get(("LOOSE", "COFACTORS"), [])]
            removed_count = original_count - len(self.atoms)
            if removed_count > 0:
                logging.info(f"Stripped off {removed_count} atoms from exposed cofactors based on SAS cutoff {sas_cutoff:.2f} in cycle {strip_tries}.")

        # debug, print out remaining atoms
        # for atom in self.atoms:
        #     print(f"{atom.resname} {atom.chain} {atom.sequence} {atom.insertion} {atom.atomname} SAS: {atom.sas:.3f}")

    def identify_ligands(self):
        """
        Identify ligands in the pdb file. The ligands detection rules are in ligand_detect_rules.ftpl
        Sample rules:
        ---------------------------------------
        LIGAND_ID, CYS, CYS: " SG " - " SG "; 2.03 +- 0.90; CYD, CYD
        LIGAND_ID, CYS, HEC: " SG " - " CA*"; 1.90 +- 1.00; CYL, HEC
        LIGAND_ID, CYS, HEM: " SG " - " CA*"; 1.90 +- 1.00; CYL, HEM
        """
        def match_strings(s1, s2):  # internal string comparison, True when match allowing "*" to match any character and length must be the same
            return all([r == "*" or s == "*" or r == s for r, s in zip(s1, s2)] + [len(s1) == len(s2)])
        
        logging.info("Identifying ligands based on LIGAND_ID rules ...")

        # Initialize SSBOND and LINK lines
        link_lines = []
        ssbond_serial = 1  # counter for SSBOND serial number starting from 1
        ssbond_fmt = "SSBOND %3d CYS %c %4d%c   CYS %c %4d%c %s  1555   1555 %5.2f\n"
        link_fmt = "LINK        %4s %3s %c%4d%c %s  %4s %3s %c%4d%c    1555   1555 %5.2f\n"
        tpl = self.tpl  # for easier access

        # Group atoms by residue
        residue_atoms_dict = defaultdict(list)
        for atom in self.atoms:
            residue_atoms_dict[(atom.resname, atom.chain, atom.sequence, atom.insertion)].append(atom)
        residue_ids = list(residue_atoms_dict.keys())       

        # Loop over residues
        for i, res1_id in enumerate(residue_ids[:-1]):
            for res2_id in residue_ids[i+1:]:
                # Check if residue pair matches any LIGAND_ID rule
                key1 = ("LIGAND_ID", res1_id[0], res2_id[0])
                key2 = ("LIGAND_ID", res2_id[0], res1_id[0])
                if key1 in tpl or key2 in tpl:  # Detected a match, either in the rule's order or the reversed order
                    res1, res2 = (res1_id, res2_id) if key1 in tpl else (res2_id, res1_id)  # assign res1 and res2 following the rule order
                    rule = tpl[key1] if key1 in tpl else tpl[key2]  # get the rule in the same order of res1, res2 as above
                    atom1_name, atom2_name = rule.atom1, rule.atom2
                    target_distance = rule.distance
                    tolerance = rule.tolerance
                    # Find the specified atoms in the residues
                    atom1_candidates = [atom for atom in residue_atoms_dict[res1] if match_strings(atom1_name, atom.atomname)]
                    atom2_candidates = [atom for atom in residue_atoms_dict[res2] if match_strings(atom2_name, atom.atomname)]
                    if not atom1_candidates or not atom2_candidates:
                        continue  # specified atoms not found in the residues
                    # Calculate distances between the specified atoms
                    for atom1 in atom1_candidates:
                        for atom2 in atom2_candidates:
                            distance = np.linalg.norm(np.array(atom1.xyz) - np.array(atom2.xyz))
                            if abs(distance - target_distance) <= tolerance:
                                # Match found, rename residues if needed
                                if atom1.resname != rule.res1_name:
                                    for atom in residue_atoms_dict[res1]:
                                        atom.resname = rule.res1_name
                                if atom2.resname != rule.res2_name:
                                    for atom in residue_atoms_dict[res2]:
                                        atom.resname = rule.res2_name
                                # Create SSBOND or LINK line
                                if rule.res1_name == "CYD" and rule.res2_name == "CYD":
                                    link_line = ssbond_fmt % (
                                        ssbond_serial,
                                        atom1.chain, atom1.sequence, atom1.insertion,
                                        atom2.chain, atom2.sequence, atom2.insertion,
                                        "SS", distance
                                    )
                                    ssbond_serial += 1
                                else:
                                    link_line = link_fmt % (
                                        atom1.atomname, atom1.resname, atom1.chain, atom1.sequence, atom1.insertion, " "*12,
                                        atom2.atomname, atom2.resname, atom2.chain, atom2.sequence, atom2.insertion,
                                        distance
                                    )
                                link_lines.append(link_line)
                                logging.info(f"    Identified ligand interaction between {atom1.resname}{atom1.chain}{atom1.sequence:04d}{atom1.insertion} and {atom2.resname}{atom2.chain}{atom2.sequence:04d}{atom2.insertion} with distance {distance:.2f} Å.")

        self.link_lines = link_lines  # Store the generated LINK and SSBOND lines
        # print link_line.strip()  # for debug
        for line in link_lines:
            logging.debug(line.strip())  # for debug

    def build_hierarchy(self):
        """Build the hierarchical structure: Protein -> Residues -> Conformers -> Atoms."""
        protein = Protein()
        residue_dict = {}
        for atom in self.atoms:
            # Find which residue the atom belongs to
            resid = (atom.resname, atom.chain, atom.sequence, atom.insertion)
            if resid not in residue_dict:
                residue = Residue()
                residue.resname, residue.chain, residue.sequence, residue.insertion = resid
                residue.resid = f"{residue.resname}{residue.chain}{residue.sequence:04d}{residue.insertion}"
                residue_dict[resid] = residue
                protein.residues.append(residue)
            else:
                residue = residue_dict[resid]
            

            # At this point, we assign all atoms to a single conformer per residue
            if not residue.conformers:
                conformer = Conformer()
                conformer.conftype = "NA"  # conformer type is not defined yet
                conformer.confnum = 0
                conformer.confid = f"{atom.resname}{conformer.conftype}{atom.chain}{atom.sequence:04d}{atom.insertion}ori"  # original conformer ID
                conformer.altloc = atom.altloc
                conformer.chain = atom.chain
                conformer.sequence = atom.sequence
                conformer.insertion = atom.insertion
                conformer.parent_residue = residue
                residue.conformers.append(conformer)
            else:
                conformer = residue.conformers[0]
            # Add atom to the conformer
            conformer.atoms.append(atom)
            atom.parent_conformer = conformer

        self.protein = protein

    def split_terminal_residues(self):
        """Split terminal residues."""
        logging.info("Splitting terminal residues ...")
        # Find chains
        chains = sorted(set(residue.chain for residue in self.protein.residues))
        
        aminoacids_in_chains = defaultdict(list)
        nonaminoacids_in_chains = defaultdict(list)

        for residue in self.protein.residues:
            if residue.resname in AMINO_ACIDS:
                aminoacids_in_chains[residue.chain].append(residue)
            else:
                nonaminoacids_in_chains[residue.chain].append(residue)
        
        # Within each chain, find terminal residues
        for chain in chains:
            aminoacids = aminoacids_in_chains[chain]  # use the original order
            if not aminoacids:
                continue  # No amino acids in this chain

            # N-terminal residue
            n_terminal_residue = aminoacids[0]
            if n_terminal_residue.resname not in TERMINAL_RESIDUES:
                ntr = Residue()
                if n_terminal_residue.resname == "GLY":
                    ntr.resname = "NTG"
                # elif n_terminal_residue.resname == "PRO":
                #     ntr.resname = "NTP" # The handling of Proline N-terminal is to be determined
                else:
                    ntr.resname = "NTR"

                ntr.chain = n_terminal_residue.chain
                ntr.sequence = n_terminal_residue.sequence
                ntr.insertion = n_terminal_residue.insertion
                ntr.resid = (ntr.resname, ntr.chain, ntr.sequence, ntr.insertion)
                ntr.conformers = []  # Will move some atoms into this new conformer of new residue

                # Move backbone atoms from the original residue to the new N-terminal residue
                ntr_conformer = Conformer()
                ntr_conformer.conftype = "NA"
                ntr_conformer.confid = f"{ntr.resname}{ntr_conformer.conftype}{ntr.chain}{ntr.sequence:04d}{ntr.insertion}ori"
                ntr_conformer.parent_residue = ntr
                ntr_conformer.atoms = [atom for atom in n_terminal_residue.conformers[0].atoms if atom.atomname in NTR_ATOMS]
                for atom in ntr_conformer.atoms:
                    atom.parent_conformer = ntr_conformer
                    atom.resname = ntr.resname  # Update atom's residue name
                # Now remove these atoms from the original residue
                n_terminal_residue.conformers[0].atoms = [atom for atom in n_terminal_residue.conformers[0].atoms if atom.atomname not in NTR_ATOMS]
                if ntr_conformer.atoms:  # Only add if there are atoms moved
                    ntr.conformers.append(ntr_conformer)
                    aminoacids.insert(0, ntr)  # Add the new N-terminal residue to the aminoacids list
                logging.info(f"    Chain {chain}: Marked N-terminal residue {n_terminal_residue.resname} {n_terminal_residue.sequence}{n_terminal_residue.insertion}")

            # C-terminal residue
            c_terminal_residue = aminoacids[-1]
            if c_terminal_residue.resname not in TERMINAL_RESIDUES:
                ctr = Residue()
                ctr.resname = "CTR"
                ctr.chain = c_terminal_residue.chain
                ctr.sequence = c_terminal_residue.sequence
                ctr.insertion = c_terminal_residue.insertion
                ctr.resid = (ctr.resname, ctr.chain, ctr.sequence, ctr.insertion)
                ctr.conformers = []  # Will move some atoms into this new conformer of new residue

                # Move backbone atoms from the original residue to the new C-terminal residue
                ctr_conformer = Conformer()
                ctr_conformer.conftype = "NA"
                ctr_conformer.confid = f"{ctr.resname}{ctr_conformer.conftype}{ctr.chain}{ctr.sequence:04d}{ctr.insertion}ori"
                ctr_conformer.parent_residue = ctr
                ctr_conformer.atoms = [atom for atom in c_terminal_residue.conformers[0].atoms if atom.atomname in CTR_ATOMS]
                for atom in ctr_conformer.atoms:
                    atom.parent_conformer = ctr_conformer
                    atom.resname = ctr.resname  # Update atom's residue name
                # Now remove these atoms from the original residue
                c_terminal_residue.conformers[0].atoms = [atom for atom in c_terminal_residue.conformers[0].atoms if atom.atomname not in CTR_ATOMS]
                if ctr_conformer.atoms:  # Only add if there are atoms moved
                    ctr.conformers.append(ctr_conformer)
                    aminoacids.append(ctr)  # Add the new C-terminal residue to the aminoacids list
                logging.info(f"    Chain {chain}: Marked C-terminal residue {c_terminal_residue.resname} {c_terminal_residue.sequence}{c_terminal_residue.insertion}")

            # Put back the updated aminoacids list to the dictionary
            aminoacids_in_chains[chain] = aminoacids

        # Rebuild the protein's residue list to include new terminal residues
        self.protein.residues = [res for chain in chains for res in aminoacids_in_chains[chain] + nonaminoacids_in_chains[chain]]


    def read_mccepdb(self, input_file: str):
        """Load an MCCE-format PDB file."""
        lines = open(input_file, 'r').readlines()
        lines = [line for line in lines if line.startswith(('ATOM  ', 'HETATM'))]
        # Convert a line to an Atom object
        atoms = []
        for line in lines:
            atom = Atom()
            atom.load_mcceline(line)
            atoms.append(atom)
        
        # Group atoms by conformer
        conformer_dict = {}
        for atom in atoms:
            confid = atom.get_confid()
            # Examples: ALABKA0122_000, GLN01A0121_001
            if confid not in conformer_dict:
                conformer = Conformer()
                conformer.confid = confid
                conformer.conftype = confid[3:5]  # e.g., BK, 01, 02, ...
                conformer.confnum = int(confid[11:])
                conformer.chain = confid[5]
                conformer.sequence = int(confid[6:10])
                conformer.insertion = confid[10]
                conformer.parent_residue = None  # to be assigned later
                conformer.atoms = []
                conformer.history = atom.history
                conformer_dict[confid] = conformer
            else:
                conformer = conformer_dict[confid]
            conformer.atoms.append(atom)
            atom.parent_conformer = conformer

        # Group conformer by residue
        residue_dict = {}
        for conformer in conformer_dict.values():
            resid = conformer.confid[0:3]+conformer.confid[5:11] # e.g., ALAA0122, GLN01A0121
            if resid not in residue_dict:
                residue = Residue()
                residue.resname = resid[0:3]
                residue.chain = resid[3]
                residue.sequence = int(resid[4:8])
                residue.insertion = resid[8]
                residue.resid = resid
                residue.conformers = []
                residue_dict[resid] = residue
            else:
                residue = residue_dict[resid]
            conformer.parent_residue = residue
            residue.conformers.append(conformer)

        # Fill the residue conformers[0] with a dummy backbone conformer if it doesn't have the backbone
        for residue in residue_dict.values():
            if residue.conformers[0].conftype != "BK":
                backbone_conformer = Conformer()
                backbone_conformer.conftype = "BK"
                backbone_conformer.confid = residue.resname + backbone_conformer.conftype + residue.chain + f"{residue.sequence:04d}" + residue.insertion + "000"
                backbone_conformer.confnum = 0
                backbone_conformer.parent_residue = residue
                backbone_conformer.history = "BKO000_000"
                backbone_conformer.atoms = []
                residue.conformers.insert(0, backbone_conformer)

        self.protein = Protein()
        self.protein.residues = list(residue_dict.values())
        logging.info(f"Loaded {len(atoms)} atoms, {len(conformer_dict)} conformers, and {len(self.protein.residues)} residues from {input_file}")


    def write_mccepdb(self, output_file: str):
        """Write the processed atoms to an MCCE format PDB file."""
        with open(output_file, 'w') as f:
            f.write("REMARK   1 Generated by pymcce\n")
            for line in self.link_lines:
                f.write(line)
            for line in self.protein.dump_lines():
                f.write(line)

        logging.info(f"Wrote MCCE-format PDB file to {output_file}")

    def assign_conftypes(self):
        """
        Assign conformer types to each residue and split sidechain conformers if alternate locations (altLoc) are present.
        - Backbone atoms are always assigned to a 'BK' conformer (slot 0).
        - Sidechain atoms are grouped by altLoc; if multiple altLocs exist, split into separate conformers.
        - Conformer types are assigned based on CONFLIST and CONNECT entries in the tpl.
        """
        for residue in self.protein.residues:
            # Each residue should have only one conformer before assignment
            if len(residue.conformers) > 1:
                logging.error(f"Residue {residue.resid} has multiple conformers before conftype assignment, which should not happen.")
                exit(1)

            # --- Backbone conformer assignment ---
            backbone_conformer = Conformer()
            backbone_conformer.conftype = "BK"
            backbone_conformer.confid = f"{residue.resname}{backbone_conformer.conftype}{residue.chain}{residue.sequence:04d}{residue.insertion}000"
            backbone_conformer.parent_residue = residue
            backbone_conformer.history = "BKO000_000"
            # Select backbone atoms using tpl CONNECT records
            backbone_atoms = [
                atom for atom in residue.conformers[0].atoms
                if ("CONNECT", atom.atomname, f"{residue.resname}BK") in self.tpl
            ]
            backbone_conformer.atoms = backbone_atoms
            residue.conformers.insert(0, backbone_conformer)
            for atom in backbone_atoms:
                atom.parent_conformer = backbone_conformer
            # Remove backbone atoms from the original conformer
            residue.conformers[1].atoms = [
                atom for atom in residue.conformers[1].atoms if atom not in backbone_atoms
            ]
            if not residue.conformers[1].atoms:
                residue.conformers.pop(1)  # Remove empty conformer

            # --- Sidechain conformer splitting by altLoc ---
            # At this point, conformers: [backbone, sidechain]
            if len(residue.conformers) == 2:
                sidechain_conformer = residue.conformers[1]
                # Group atoms by altLoc
                altloc_dict = defaultdict(list)
                for atom in sidechain_conformer.atoms:
                    altloc_dict[atom.altloc].append(atom)
                # If altLoc ' ' exists, treat as common atoms and add to all altLoc groups
                if " " in altloc_dict:
                    common_atoms = altloc_dict.pop(" ")
                    for altloc in altloc_dict:
                        altloc_dict[altloc] = copy.deepcopy(common_atoms) + altloc_dict[altloc]
                # If multiple altLocs, split into separate conformers
                if len(altloc_dict) > 1:
                    residue.conformers.pop(1)  # Remove original sidechain conformer
                    for altloc, atoms in altloc_dict.items():
                        new_conformer = Conformer()
                        new_conformer.conftype = "NA"  # Not assigned yet
                        new_conformer.confid = f"{residue.resname}{new_conformer.conftype}{residue.chain}{residue.sequence:04d}{residue.insertion}000"
                        new_conformer.parent_residue = residue
                        new_conformer.history = f"{new_conformer.conftype}{altloc}000_000"
                        new_conformer.atoms = atoms
                        for atom in atoms:
                            atom.parent_conformer = new_conformer
                        residue.conformers.append(new_conformer)
                    logging.info(f"Residue {residue.resid}: Split sidechain into {len(altloc_dict)} conformers based on altLoc.")
                else:
                    # Only one altLoc, assign default type
                    sidechain_conformer.conftype = "NA"
                    sidechain_conformer.confid = f"{residue.resname}{sidechain_conformer.conftype}{residue.chain}{residue.sequence:04d}{residue.insertion}000"
                    sidechain_conformer.parent_residue = residue
                    sidechain_conformer.history = f"{sidechain_conformer.conftype}O000_000"
            elif len(residue.conformers) > 2:
                logging.error(f"Residue {residue.resid} has more than two conformers before conftype assignment, which should not happen.")
                exit(1)

            # --- Assign conformer types based on tpl CONFLIST and CONNECT ---
            # Backbone conformer is always 'BK'; assign types to sidechain conformers
            if len(residue.conformers) > 1:
                key = ("CONFLIST", residue.resname)
                possible_conftypes = self.tpl.get(key, [])
                if not possible_conftypes:
                    # Unknown residue: assign '??' type
                    logging.warning(
                        f"Unknown residue {residue.resname}. No charges are assigned. Use mccetools to generate a ftpl file."
                    )
                    for conformer in residue.conformers[1:]:
                        conformer.conftype = "??"
                        conformer.confid = f"{residue.resname}{conformer.conftype}{residue.chain}{residue.sequence:04d}{residue.insertion}000"
                        conformer.history = f"{conformer.conftype}{conformer.history[2:]}"
                else:
                    # Assign type by matching all atoms to a CONNECT entry for each possible conftype
                    for conformer in residue.conformers[1:]:
                        assigned_type = "NA"  # Default type
                        for conftype in possible_conftypes:
                            if all(
                                ("CONNECT", atom.atomname, conftype) in self.tpl
                                for atom in conformer.atoms
                            ):
                                assigned_type = conftype[-2:]  # Use last two characters of conftype
                                break
                        conformer.conftype = assigned_type
                        conformer.confid = f"{residue.resname}{conformer.conftype}{residue.chain}{residue.sequence:04d}{residue.insertion}000"
                        conformer.history = f"{conformer.conftype}{conformer.history[2:]}"


    def write_head1_lst(self, head1_file):
        """Write head1.lst: summary of residues for step 2."""
        with open(head1_file, "w") as f:
            f.write("#Rotamer Making Site Specific Instruction:\n")
            for res in self.protein.residues:
                insertion = res.insertion if res.insertion != "_" else " "
                f.write(f"{res.resname} {res.chain}{res.sequence:4d} {insertion} R f 00 S f 0.0 H f\n")


    # This section contains methods to make atom connections.
    # ---------------------------------------------------------------------------------
    # Connections are stored in each Atom object as lists of connected atom indices:
    # connect12: list of indices of atoms directly bonded (1-2 connections)
    # connect13: list of indices of atoms bonded to connect12 atoms (1-3 connections)
    # connect14: list of indices of atoms bonded to connect13 atoms (1-4 connections)
    #
    # connect13 and connect14 are derived from connect12.
    # connect12 is determined based on both topology (from tpl CONNECT records) and distance criteria.
    # Backbone atoms are connected only to other backbone atoms and CTR/NTR atoms.
    # Sidechain atoms are connected within the conformer and to the backbone atoms (this breaks the connect symmetry but prevents circular connect).
    # ---------------------------------------------------------------------------------
    def reset_connect(self):
        """Reset all atom connections."""
        for residue in self.protein.residues:
            for conformer in residue.conformers:
                for atom in conformer.atoms:
                    atom.connect12 = []
                    atom.connect13 = []
                    atom.connect14 = []


    def make_connect12(self):
        """Make 1-2 connections based on both conformer topology and distance criteria."""
        self.reset_connect()
        logging.debug("Making 1-2 connections ...")
        tpl = self.tpl  # for easier access
        bonding_tolerance = 0.20  # Angstrom, tolerance added to the average of covalent radii to determine bonding

        # Connectivity assignment logic:
        # 1. For each atom, use CONNECT definitions to find named bonded atoms within the same conformer and add them to connect12.
        # 2. If the CONNECT definition includes "?", search for matching ligated atoms outside the residue (i.e., in other residues) that also have "?" in their CONNECT definition.
        # 3. NTR and CTR residues require special handling: their atoms connect to backbone atoms of the next or previous residue, even if not matching "?" is present in those residues.
        # 4. For SG in CYL, handle the case where it connects to "?" but the ligated atom does not have "?" in its own CONNECT definition.
        for ires, residue in enumerate(self.protein.residues):
            for conformer in residue.conformers:
                for atom in conformer.atoms:
                    key = ("CONNECT", atom.atomname, f"{residue.resname}{conformer.conftype}")
                    connect_params = tpl.get(key, None)
                    if connect_params is not None:
                        bonded_atom_names = [entry for entry in connect_params.connected]
                        for bonded_name in bonded_atom_names:
                            if "?" in bonded_name:  # Unnamed atom connection, need to search outside the residue
                                # If this is a backbone atom, only search previous or next residue on specific atoms
                                if conformer.conftype == "BK":
                                    # CONNECT, " N  ", ASNBK: sp2, " ?  ", " CA ", " H  "
                                    # CONNECT, " H  ", ASNBK: s, " N  "
                                    # CONNECT, " CA ", ASNBK: sp3, " N  ", " C  ", " CB ", " HA "
                                    # CONNECT, " HA ", ASNBK: s, " CA "
                                    # CONNECT, " C  ", ASNBK: sp2, " CA ", " O  ", " ?  "
                                    # CONNECT, " O  ", ASNBK: sp2, " C  "
                                    # " N  " connects to " C  " of the previous residue
                                    # " C  " connects to " N  " of the next residue
                                    if atom.atomname == " N  ":
                                        if ires > 0:
                                            prev_residue = self.protein.residues[ires - 1]
                                            if prev_residue.chain == residue.chain:
                                                # Look for the previous residue's C atom in backbone 
                                                for prev_atom in prev_residue.conformers[0].atoms:
                                                    if prev_atom.atomname == " C  ":
                                                        distance = np.linalg.norm(np.array(atom.xyz) - np.array(prev_atom.xyz))
                                                        covalent_avg = (ATOM_RADII.get(atom.element, ATOM_RADIUS_UNKNOWN) + ATOM_RADII.get(prev_atom.element, ATOM_RADIUS_UNKNOWN))/2
                                                        if distance <= covalent_avg + bonding_tolerance:
                                                            if prev_atom not in atom.connect12:
                                                                atom.connect12.append(prev_atom)
                                                            if atom not in prev_atom.connect12:
                                                                prev_atom.connect12.append(atom)
                                                            logging.debug(f"Connected {atom.atomname} ({residue.resid}) to previous C {prev_atom.atomname} ({prev_residue.resname}{prev_residue.chain}{prev_residue.sequence:04d}{prev_residue.insertion}) at {distance:.2f} Å.")
                                                        # Once we handled the C atom, stop searching further
                                                        break
                                    elif atom.atomname == " C  ":
                                        if ires < len(self.protein.residues) - 1:
                                            next_residue = self.protein.residues[ires + 1]
                                            if next_residue.chain == residue.chain:
                                                # Look for next residue's N atom in backbone
                                                for next_atom in next_residue.conformers[0].atoms:
                                                    if next_atom.atomname == " N  ":
                                                        distance = np.linalg.norm(np.array(atom.xyz) - np.array(next_atom.xyz))
                                                        covalent_ave = (ATOM_RADII.get(atom.element, ATOM_RADIUS_UNKNOWN) + ATOM_RADII.get(next_atom.element, ATOM_RADIUS_UNKNOWN)) / 2
                                                        if distance <= covalent_ave + bonding_tolerance:
                                                            if next_atom not in atom.connect12:
                                                                atom.connect12.append(next_atom)
                                                            if atom not in next_atom.connect12:
                                                                next_atom.connect12.append(atom)
                                                            logging.debug(f"Connected {atom.atomname} ({residue.resid}) to next N {next_atom.atomname} ({next_residue.resname}{next_residue.chain}{next_residue.sequence:04d}{next_residue.insertion}) at {distance:.2f} Å.")

                                # If this is a sidechain atom, search all residues for possible ligands
                                else:
                                    for other_residue in self.protein.residues:
                                        if other_residue == residue:
                                            continue  # Skip same residue
                                        for other_conformer in other_residue.conformers:
                                            for other_atom in other_conformer.atoms:
                                                other_key = ("CONNECT", other_atom.atomname, f"{other_residue.resname}{other_conformer.conftype}")
                                                other_connect_params = tpl.get(other_key, None)
                                                if other_connect_params is not None and any(a.strip() == "?" for a in other_connect_params.connected):
                                                    # Check distance criterion
                                                    distance = np.linalg.norm(np.array(atom.xyz) - np.array(other_atom.xyz))
                                                    covalent_avg = (ATOM_RADII.get(atom.element, ATOM_RADIUS_UNKNOWN) + ATOM_RADII.get(other_atom.element, ATOM_RADIUS_UNKNOWN)) / 2
                                                    if distance <= covalent_avg + bonding_tolerance:
                                                        # NTR/NTG -> next residue backbone connection


                                                        # CTR -> previous residue backbone connection


                                                        if other_atom not in atom.connect12:
                                                            atom.connect12.append(other_atom)
                                                        if atom not in other_atom.connect12:
                                                            other_atom.connect12.append(atom)
                                                        logging.debug(f"Connected {atom.atomname} ({residue.resid}) to {other_atom.atomname} ({other_residue.resid}) via '?' match at distance {distance:.2f} Å.")
                                                elif residue.resname in ("CYL") and atom.atomname in (" SG ") and bonded_name.strip() == "?":
                                                    # Special case for CYL SG atom, or cases that a "?" bonded atom connects to a named atom
                                                    distance = np.linalg.norm(np.array(atom.xyz) - np.array(other_atom.xyz))
                                                    covalent_avg = (ATOM_RADII.get(atom.element, ATOM_RADIUS_UNKNOWN) + ATOM_RADII.get(other_atom.element, ATOM_RADIUS_UNKNOWN)) / 2
                                                    if distance <= covalent_avg + bonding_tolerance:
                                                        if other_atom not in atom.connect12:
                                                            atom.connect12.append(other_atom)
                                                        if atom not in other_atom.connect12:
                                                            other_atom.connect12.append(atom)
                                                # else:
                                                #     print(conformer.confid, atom.atomname, other_atom.atomname, bonded_name.strip())
                            else:  # Named atom connection within the same conformer or to backbone/NTR/CTR
                                # Search within the same conformer first
                                found = False
                                for target_atom in conformer.atoms:
                                    if target_atom.atomname == bonded_name and target_atom != atom:
                                        if atom not in target_atom.connect12:
                                            target_atom.connect12.append(atom)
                                            logging.debug(f"target_atom.connect12 after append: {target_atom.connect12}")
                                        if target_atom not in atom.connect12:
                                            atom.connect12.append(target_atom)
                                            logging.debug(f"atom.connect12 after append: {atom.connect12}")
                                        found = True
                                        logging.debug(f"Connected {atom.atomname} to {target_atom.atomname} within the same conformer.")
                                # If not found, search named atom in backbone. This is redundant for backbone atoms but for coding simplicity we do it anyway.
                                if not found:
                                    for backbone_atom in residue.conformers[0].atoms:  # Backbone is always the first conformer
                                        if backbone_atom.atomname == bonded_name and backbone_atom != atom:
                                            if atom not in backbone_atom.connect12:
                                                backbone_atom.connect12.append(atom)
                                            if backbone_atom not in atom.connect12:
                                                atom.connect12.append(backbone_atom)
                                            found = True
                                            logging.debug(f"Connected {atom.atomname} to backbone atom {backbone_atom.atomname}.")
                                # If a named atom is still not found, check if it is bonded to NTR/CTR
                                if not found:
                                    # Named atom " CA " could be on NTR/NTG
                                    if bonded_name == " CA ":
                                        if ires > 0:  # Not the first residue
                                            prev_residue = self.protein.residues[ires - 1]
                                            if prev_residue.chain == residue.chain and prev_residue.resname in ("NTR", "NTG"):
                                                for conformer_in_prev_residue in prev_residue.conformers:
                                                    for prev_residue_atom in conformer_in_prev_residue.atoms:
                                                        if prev_residue_atom.atomname == " CA ":
                                                            if atom not in prev_residue_atom.connect12:
                                                                prev_residue_atom.connect12.append(atom)
                                                            if prev_residue_atom not in atom.connect12:
                                                                atom.connect12.append(prev_residue_atom)
                                                        found = True
                                                        logging.debug(f"Connected {atom.atomname} to NTR/NTG atom {prev_residue_atom.atomname} from {conformer_in_prev_residue.confid} previous residue.")                                    
                                    # Named atom " C  " could be on CTR
                                    elif bonded_name == " C  ":
                                        if ires < len(self.protein.residues) - 1:  # Not the last residue
                                            next_residue = self.protein.residues[ires + 1]
                                            if next_residue.chain == residue.chain and next_residue.resname == "CTR":
                                                for conformer_in_next_residue in next_residue.conformers:
                                                    for next_residue_atom in conformer_in_next_residue.atoms:
                                                        if next_residue_atom.atomname == " C  ":
                                                            if atom not in next_residue_atom.connect12:
                                                                next_residue_atom.connect12.append(atom)
                                                            if next_residue_atom not in atom.connect12:
                                                                atom.connect12.append(next_residue_atom)
                                                        found = True
                                                        logging.debug(f"Connected {atom.atomname} to CTR atom {next_residue_atom.atomname} from {conformer_in_next_residue.confid} next residue.")  
                                if not found:
                                    # A named atom is not found in the same conformer, backbone, or NTR/CTR. This could be an error in the tpl file or an unusual residue.
                                    if conformer.conftype == "BK" or is_H(bonded_name):
                                        # It's acceptable for backbone atoms or hydrogens to not find all named connections
                                        logging.debug(f"A named atom '{bonded_name}' for {atom.atomname} in residue {residue.resid} not found. This is acceptable for backbone atoms or hydrogens.")
                                    else:
                                        logging.debug(f"A named atom '{bonded_name}' for {atom.atomname} in residue {residue.resid} not found.")

    def check_connect_symmetry(self):
        """Check the symmetry of connect12 for all atoms."""
        logging.info("Checking connect12 symmetry because it's critically important ...")
        passed = True
        for residue in self.protein.residues:
            for conformer in residue.conformers:
                for atom in conformer.atoms:
                    for bonded_atom in atom.connect12:
                        if atom not in bonded_atom.connect12:
                            passed = False
                            logging.warning(f"Connect12 asymmetry: {atom.atomname} ({residue.resid}) connected to {bonded_atom.atomname} ({bonded_atom.parent_conformer.parent_residue.resid}), but not vice versa.")

        if passed:
            logging.info("Connect12 symmetry check passed.")
        else:
            logging.error("Connect12 symmetry check failed.")

    def make_connect13(self):
        """Make 1-3 connections based on 1-2 connections. Do not include atoms in different side chain conformers of the same residue."""
        logging.debug("Making 1-3 connections ...")
        for residue in self.protein.residues:
            for conformer in residue.conformers:
                for atom in conformer.atoms:
                    # Local references to avoid repeated attribute lookups
                    conn12 = atom.connect12
                    if not conn12:
                        atom.connect13 = []
                        continue

                    # Build candidate set: all atoms connected to any 1-2 neighbor
                    conn12_set = set(conn12)
                    candidates = set()
                    for a2 in conn12:
                        candidates.update(a2.connect12)

                    # Remove self and direct neighbors
                    candidates.difference_update(conn12_set)
                    candidates.discard(atom)

                    # Pre-cache parent references for quick checks
                    atom_parent_res = atom.parent_conformer.parent_residue
                    atom_parent_conf = atom.parent_conformer
                    atom_is_bk = (atom_parent_conf.conftype == "BK")

                    # Filter candidates according to allowed rules and preserve uniqueness
                    filtered = []
                    for a3 in candidates:
                        a3_parent_conf = a3.parent_conformer
                        a3_parent_res = a3_parent_conf.parent_residue
                        # Allowed if:
                        # - different residue, OR
                        # - same conformer, OR
                        # - either conformer is backbone ("BK")
                        if (a3_parent_res is not atom_parent_res) or \
                           (a3_parent_conf is atom_parent_conf) or \
                           atom_is_bk or \
                           (a3_parent_conf.conftype == "BK"):
                            filtered.append(a3)

                    atom.connect13 = filtered

    def make_connect14(self):
        """Make 1-4 connections based on 1-2 and 1-3 connections. Do not include atoms in different side chain conformers of the same residue."""
        logging.debug("Making 1-4 connections ...")
        for residue in self.protein.residues:
            for conformer in residue.conformers:
                for atom in conformer.atoms:
                    conn13 = atom.connect13
                    if not conn13:
                        atom.connect14 = []
                        continue

                    # Precompute sets and locals to avoid repeated attribute lookup
                    atom_connect12_set = set(atom.connect12)
                    atom_connect13_set = set(conn13)
                    atom_parent_res = atom.parent_conformer.parent_residue
                    atom_parent_conf = atom.parent_conformer
                    atom_is_bk = (atom_parent_conf.conftype == "BK")

                    # Collect all possible atom4 candidates once (unique)
                    candidates = set()
                    for a3 in conn13:
                        candidates.update(a3.connect12)

                    # Exclude atom itself and direct neighbors and 1-3 neighbors
                    candidates.discard(atom)
                    candidates -= atom_connect12_set
                    candidates -= atom_connect13_set

                    # Filter candidates according to allowed rules and preserve insertion order roughly
                    conn14_list = []
                    seen = set()
                    for a4 in candidates:
                        a4_parent_conf = a4.parent_conformer
                        if (a4_parent_conf.parent_residue is not atom_parent_res) or \
                           (a4_parent_conf is atom_parent_conf) or \
                           atom_is_bk or \
                           (a4_parent_conf.conftype == "BK"):
                            if a4 not in seen:
                                seen.add(a4)
                                conn14_list.append(a4)

                    atom.connect14 = conn14_list

    def dump_connectivity(self):
        """Dump connectivity information for debugging."""
        logging.info("Dumping connectivity information to %s...", CONNECT_TABLE)
        with open(CONNECT_TABLE, "w") as f:
            for residue in self.protein.residues:
                for conformer in residue.conformers:
                    for atom in conformer.atoms:
                        f.write(f"Residue {residue.resid}, Conformer {conformer.confid}, Atom {atom.atomname}:\n")
                        f.write(f"CONNECT12 \"{atom.atomname}\" {conformer.confid}: {[f'"{a.atomname}"({a.parent_conformer.confid})' for a in atom.connect12]}\n")
                        f.write(f"CONNECT13 \"{atom.atomname}\" {conformer.confid}: {[f'"{a.atomname}"({a.parent_conformer.confid})' for a in atom.connect13]}\n")
                        f.write(f"CONNECT14 \"{atom.atomname}\" {conformer.confid}: {[f'"{a.atomname}"({a.parent_conformer.confid})' for a in atom.connect14]}\n")



    def place_oxt(self):
        n_placed = 0
        # Place OXT on CTRs if missing
        for residue in self.protein.residues:
            if residue.resname == "CTR":
                for conformer in residue.conformers[1:]:  # Skip backbone conformer
                    has_oxt = any(atom.atomname == " OXT" for atom in conformer.atoms)
                    if not has_oxt:
                        # Find the C atom to attach OXT
                        c_atom = next((atom for atom in conformer.atoms if atom.atomname == " C  "), None)
                        if c_atom is not None:
                            connected_hv_atoms = [atom for atom in c_atom.connect12 if atom.element in (" O", " N", " S", " C")]
                            if len(connected_hv_atoms) >= 2:
                                # Calculate the position of OXT based on the positions of C and its connected heavy atoms
                                vec_sum = np.zeros(3)
                                for hv_atom in connected_hv_atoms:
                                    vec = np.array(c_atom.xyz) - np.array(hv_atom.xyz)
                                    vec_sum += vec / np.linalg.norm(vec)
                                vec_sum /= np.linalg.norm(vec_sum)
                                oxt_position = np.array(c_atom.xyz) + vec_sum * 1.24  # Approximate C-O bond length
                                # Create OXT atom
                                oxt_atom = Atom()
                                oxt_atom.record = "ATOM  "
                                oxt_atom.atomname = " OXT"
                                oxt_atom.resname = residue.resname
                                oxt_atom.chain = residue.chain
                                oxt_atom.sequence = residue.sequence
                                oxt_atom.insertion = residue.insertion
                                oxt_atom.element = " O"
                                oxt_atom.xyz = tuple(oxt_position)
                                oxt_atom.r_boundary = ATOM_RADII.get(oxt_atom.element, ATOM_RADIUS_UNKNOWN)
                                oxt_atom.parent_conformer = conformer
                                conformer.atoms.append(oxt_atom)
                                # Add connectivity between OXT and C atom
                                oxt_atom.connect12.append(c_atom)
                                c_atom.connect12.append(oxt_atom)
                                n_placed += 1
                                logging.info(f"Placed missing OXT for {conformer.confid} at ({oxt_atom.xyz[0]:.3f}, {oxt_atom.xyz[1]:.3f}, {oxt_atom.xyz[2]:.3f}).")
                            else:
                                logging.warning(f"Cannot place OXT for {conformer.confid} because C atom has insufficient heavy atom connections.")
                        else:
                            logging.warning(f"Cannot place OXT for {conformer.confid} because C atom is missing.")

        return n_placed

    def load_ideal_structures(self, folder: str) -> dict[str, dict[str, tuple[float, float, float]]]:
        """Load ideal structures from the specified folder.

        Args:
            folder (str): Path to the folder containing ideal structure PDB files.

        Returns:
            Dict[str, Dict[str, Tuple[float, float, float]]]: A dictionary mapping residue names to their ideal atom coordinates.
        """
        ideal_structures = {}
        folder_path = Path(folder)
        for pdb_path in folder_path.glob("*.pdb"):
            with pdb_path.open() as f:
                for line in f:
                    if line.startswith(("HETATM", "ATOM  ")):
                        atom = Atom()
                        atom.load_pdbline(line)
                        if atom.element != " H":
                            ideal_structures.setdefault(atom.resname, {})[atom.atomname] = atom.xyz
        return ideal_structures
    

    def write_rot_stat(self, step=None, rot_stat_file: str = None):        
        """Write rotamer statistics to a file."""
        if step is None:  # Initialize counts to zero and nothing else
            self.res_rot_stat = [ROT_STAT_item() for _ in self.protein.residues]  # a list of ROT_STAT_item of residues
            return

        if not self.res_rot_stat: # Safety check in case no residues exist
            logging.warning("No residues to process for rotamer statistics.")
            return

        header = "  Residue  Start   Swap Rotate  Clean Hbond  Repack Xposed   Ioni   TorH     OH Cluster\n"
        # Aggregate statistics from conformers
        attributes = list(vars(self.res_rot_stat[0]).keys())
        if step in attributes:
            for i_res in range(len(self.protein.residues)):
                n_conf = len(self.protein.residues[i_res].conformers)-1  # side chain conformers
                if n_conf < 0:
                    n_conf = 0
                    logging.warning("Detected 0 conformer residue %s" % self.protein.residues[i_res].resid)
                setattr(self.res_rot_stat[i_res], step, n_conf)
        else:
            logging.warning(f"Rotamer statistics step '{step}' is not recognized.")
 

        self.total_conf = ROT_STAT_item()
        lines = [header]
        for i_res, residue in enumerate(self.protein.residues):
            res_name = residue.resid #"%3s%c%04d%c" % residue.resid
            stat = self.res_rot_stat[i_res]
            line = "%9s %6d %6d %6d %6d %6d %6d %6d %6d %6d %6d %6d\n" % (res_name,
                                                                              stat.start,
                                                                              stat.swap,
                                                                              stat.rotate,
                                                                              stat.clean,
                                                                              stat.hbond,
                                                                              stat.repack,
                                                                              stat.xposed,
                                                                              stat.ioni,
                                                                              stat.torh,
                                                                              stat.oh,
                                                                              stat.cluster)            
            for attr in attributes:
                setattr(self.total_conf, attr, getattr(self.total_conf, attr) + getattr(stat, attr))
            lines.append(line)
        lines.append("-"*len(header.rstrip('\n')) + "\n")

        line = "%9s %6d %6d %6d %6d %6d %6d %6d %6d %6d %6d %6d\n" % ("Total",
                                                                          self.total_conf.start,
                                                                          self.total_conf.swap,
                                                                          self.total_conf.rotate,
                                                                          self.total_conf.clean,
                                                                          self.total_conf.hbond,
                                                                          self.total_conf.repack,
                                                                          self.total_conf.xposed,
                                                                          self.total_conf.ioni,
                                                                          self.total_conf.torh,
                                                                          self.total_conf.oh,
                                                                          self.total_conf.cluster)
        lines.append(line)

        if rot_stat_file is not None:
            with open(rot_stat_file, "w") as f:
                f.writelines(lines)
        else:
            logging.warning("No rot_stat_file specified; skipping writing rotamer statistics.")
        
    def rot_swap(self):
        """
        Generate swap rotamers for sidechain conformers based on ROT_SWAP rules defined in ftpl files.

        ROT_SWAP rules specify pairs of atom names within a residue that can be swapped to create new rotamer conformers.
        For each residue with a ROT_SWAP rule, this method examines all sidechain conformers (excluding backbone),
        and for each, creates a new conformer where all present swap pairs are simultaneously swapped.

        The swap is performed by exchanging the coordinates, boundary radii, and charges of the atoms in each swap pair.
        The new conformer's history string is modified by setting position 2 to 'W', indicating it was generated by a swap.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Example
        -------
        Suppose a residue has a ROT_SWAP rule for atoms 'CD' and 'CE'. For each sidechain conformer containing both atoms,
        a new conformer is created where the coordinates, boundary radii, and charges of 'CD' and 'CE' are swapped.
        The new conformer is appended to the residue's conformer list, and its history string's third character is set to 'W'.

        Notes
        -----
        - The method does not require connectivity information, but resets it to ensure deepcopy works correctly.
        - Only conformers with all swap pairs present are considered for swapping.
        - The backbone conformer (index 0) is ignored.
        """
        self.reset_connect()   # We do not need connectivity for rotamer swap, but reset it so that deepcopy works correctly
        for res in self.protein.residues:
            key = ("ROT_SWAP", res.resname)
            if key in self.tpl:
                # For each residue with a ROT_SWAP rule, perform simultaneous swaps:
                # collect all swap pairs, and for each existing sidechain conformer, create one new conformer
                # that swaps all present pairs at the same time.
                swap_pairs = self.tpl[key].swapables
                nconf = len(res.conformers)
                for i_conf in range(1, nconf):  # ignore the backbone conformer
                    conf = res.conformers[i_conf]
                    # Build a map of atomname -> atom for the original conformer
                    orig_atoms_by_name = {atom.atomname: atom for atom in conf.atoms}
                    # Determine which pairs are present and build a swap mapping
                    swap_map = {}
                    for atom1_name, atom2_name in swap_pairs:
                        if atom1_name in orig_atoms_by_name and atom2_name in orig_atoms_by_name:
                            swap_map[atom1_name] = atom2_name
                            swap_map[atom2_name] = atom1_name
                    # If no pairs found in this conformer, skip
                    if not swap_map:
                        continue
                    # Capture original attributes for involved atom names so swaps use original values
                    original_attrs = {}
                    for name in set(swap_map.keys()):
                        a = orig_atoms_by_name.get(name)
                        if a is not None:
                            original_attrs[name] = (a.xyz, a.r_boundary, a.charge)
                    # Create one deepcopy and apply all swaps based on original attributes
                    new_conf = copy.deepcopy(conf)
                    new_conf.history = conf.history[:2] + "W" + conf.history[3:]
                    for new_atom in new_conf.atoms:
                        partner_name = swap_map.get(new_atom.atomname)
                        if partner_name and partner_name in original_attrs:
                            xyz, r_boundary, charge = original_attrs[partner_name]
                            new_atom.xyz = xyz
                            new_atom.r_boundary = r_boundary
                            new_atom.charge = charge
                        # new_atom.parent_conformer = new_conf  # This is handled by deepcopy

                    # insert this new conf (one per original conformer with any swaps)
                    res.conformers.append(new_conf)

    def conf_swing(self, conf, angle=10.0, heavy_atom_only: bool = True) -> list:
        """Generate swing rotamers for a single conformer.

        Args:
            conf: The seed conformer to generate swing rotamers from.
            angle (float): The angle in degrees by which to swing the rotatable group(s).
            heavy_atom_only (bool): If True, only heavy atoms are considered during swinging.

        Returns:
            list: A list of new conformers generated from the input conformer.
        """
        new_confs = []   # store all newly generated conformers from this seed conformer
        conftype = f"{conf.parent_residue.resname}{conf.conftype}"
        if conftype in self.rotate_rules:
            rules = self.rotate_rules[conftype]
            for rule in rules:
                confs_base = [conf] + new_confs  # start from the original conformer and all newly generated conformers
                for each_conf in confs_base:
                    for direction in (+1, -1):
                        new_conf = swing_a_conformer(each_conf, rule, angle_deg=direction * angle, heavy_atom_only=heavy_atom_only)
                        if new_conf is not None:
                            new_confs.append(new_conf)
        return new_confs


    def rot_swing(self, heavy_atom_only: bool = True) -> int:
        n_new = 0
        self.reset_connect()   
        self.make_connect12()  # needed for rotate
        angle = float(self.prm.get("PHI_SWING", "10.0"))  # default 10 degrees
        for res in self.protein.residues:
            added_confs_to_res = []
            for conf in res.conformers[1:]:  # skip backbone conformer
                new_confs = self.conf_swing(conf, angle=angle, heavy_atom_only=heavy_atom_only)
                n_new += len(new_confs)                
                added_confs_to_res.extend(new_confs)
            res.conformers.extend(added_confs_to_res)

        return n_new
    

    def rot_rotate(self, heavy_atom_only: bool = True) -> int:
        n_new = 0
        self.reset_connect()   
        self.make_connect12()  # needed for rotate
        n_steps = int(self.prm.get("ROTATIONS", "6"))  # default 6 steps
        angle = 360.0 / n_steps
        for res in self.protein.residues:
            added_confs_to_res = []
            for conf in res.conformers[1:]:  # skip backbone conformer
                # make a atom name to atom mapping for this conformer
                new_confs = []   # store all newly generated conformers from this seed conformer
                conftype = f"{res.resname}{conf.conftype}"
                if conftype in self.rotate_rules:
                    rules = self.rotate_rules[conftype]
                    for rule in rules:
                        confs_base = [conf] + new_confs  # start from the original conformer and all newly generated conformers
                        for each_conf in confs_base:
                            for i in range(1, n_steps):  # skip 0 degree rotation
                                new_conf = swing_a_conformer(each_conf, rule, angle_deg=i*angle, heavy_atom_only=heavy_atom_only)
                                if new_conf is not None:
                                    new_confs.append(new_conf)
                n_new += len(new_confs)                
                added_confs_to_res.extend(new_confs)
            res.conformers.extend(added_confs_to_res)

        return n_new

    def assign_radii(self):
        """Assign radii to all atoms."""
        for residue in self.protein.residues:
            for conformer in residue.conformers:
                for atom in conformer.atoms:
                    key = ("RADIUS", residue.resname+conformer.conftype, atom.atomname)
                    r_param = self.tpl.get(key, None)
                    if r_param is not None:
                        atom.r_boundary = r_param.r_bound
                        atom.r_vdw = r_param.r_vdw
                        atom.e_vdw = r_param.e_vdw
                    else:
                        r_param_default = ATOM_RADII_VDW_DEFAULT.get(atom.element, ATOM_RADII_VDW_DEFAULT_UNKNOWN)
                        logging.info(f"No radius param for key: {key}. Using default radius.")
                        atom.r_boundary = r_param_default[0]
                        atom.r_vdw = r_param_default[1]
                        atom.e_vdw = r_param_default[2]

    def assign_charges(self):
        """Assign charges to all atoms."""
        for residue in self.protein.residues:
            for conformer in residue.conformers:
                for atom in conformer.atoms:
                    key = ("CHARGE", residue.resname+conformer.conftype, atom.atomname)
                    atom.charge = self.tpl.get(key, 0.0)  # default charge 0.0


    def self_clean(self) -> int:
        """
        Clean conformers by removing those with high self van der Waals energy.
        Use VDW_CUTOFF from prm file as the threshold.
        Consider only heavy atoms for self VDW calculation.
        Always keep the native conformers (history string). 
        """
        protein = self.protein
        vdw_cutoff = float(self.prm.get("VDW_CUTOFF", "10.0"))  # default 10.0 kcal/mol
        n_removed_total = 0
        
        # Filter out H atoms
        for residue in protein.residues:
            for conformer in residue.conformers:
                conformer.atoms = [atom for atom in conformer.atoms if atom.element != " H"]
        
        # Necessary preparations
        self.reset_connect()
        self.make_connect12()  # needed for VDW calculation
        self.make_connect13()
        self.make_connect14()
        self.assign_radii()  # needed for VDW calculation

        logging.info("Starting self VDW energy calculation for self_clean ...")
        # Each conformer is checked for self VDW energy + backbone VDW energy
        # collect backbone atoms 
        backbone_atoms = []
        for residue in protein.residues:
            for atom in residue.conformers[0].atoms:  # backbone is always the first conformer
                backbone_atoms.append(atom)

        # Now check each conformer
        for residue in protein.residues:
            for conformer in residue.conformers[1:]:  # skip backbone conformer
                conformer.is_native = len(conformer.history) >= 3 and conformer.history[2] in HISTORY_NATIVE
                self_vdw_energy = 0.0
                if len(conformer.atoms) > 0:
                    conformer_atoms = [atom for atom in conformer.atoms]  # already filtered H atoms
                    # Self VDW energy
                    self_vdw_energy += 0.5 * vdw_atoms_to_atoms(conformer_atoms, conformer_atoms)  # self VDW counts each pair twice
                    # Backbone VDW energy
                    self_vdw_energy += vdw_atoms_to_atoms(conformer_atoms, backbone_atoms)
                conformer.self_vdw_energy = self_vdw_energy
            min_vdw_energy = min((conf.self_vdw_energy for conf in residue.conformers[1:]), default=0.0)
            # Keep backbone and any sidechain conformer that is native or within the VDW cutoff
            threshold = min_vdw_energy + vdw_cutoff
            filtered_conformers = [residue.conformers[0]] + [
                conf for conf in residue.conformers[1:]
                if conf.is_native or conf.self_vdw_energy <= threshold
            ]
            n_removed_total += len(residue.conformers) - len(filtered_conformers)
            residue.conformers = filtered_conformers

        return n_removed_total


    def hbond_directed_rotamers(self) -> int:
        """
        Generate Hbond directed rotamers for residues with atoms that can form hydrogen bonds.
        Criteria for Hbond atoms:
        - Atom element is in HBOND_ATOM_ELEMENTS
        - Atom charge is more negative than HBOND_ATOM_CHARGE
        - There exists a potential Hbond acceptor/donor atom in another residue within HBOND_DISTANCE_INI2

        The new rotamer is generated by adjusting the position of the Hbond atom to bring it closer to the target atom,
        aiming for a final distance of HBOND_DISTANCE_END2.

        Returns:
            int: The number of new Hbond directed rotamers generated.
        """

        n_new_rotamers = 0

        # Necessary preparations
        self.assign_charges()
        self.reset_connect()
        self.make_connect12()  # needed for rotate

        # Helper classes and functions
        class Hbond_Element:    # one Hbond screen candidate is a pair of atom and the conformer it belongs to.
            def __init__(self, atom, conf, res):
                self.atom = atom         
                self.conf = conf
                self.res = res

        def ddvv(v1, v2):
            """ Calculate squared distance between two 3D vectors.
            """
            return (v1[0]-v2[0])**2 + (v1[1]-v2[1])**2 + (v1[2]-v2[2])**2

        def look_for_hbond(self, c1, c2):
            """ Based on candidates c1 and c2, find optimized pair of conformers.
            Improved version with caching and vectorized distance checks to reduce repeated swings.
            """
            base_pair = (c1, c2)  # optimized pair
            d2 = ddvv(c1.atom.xyz, c2.atom.xyz)
            base_doff = abs(d2 - HBOND_DISTANCE_END2)

            # quick reject: same conformer or too far
            if c1.conf == c2.conf or d2 >= HBOND_DISTANCE_INI2:
                return None

            # ensure cache container exists on self
            if not hasattr(self, "_conf_swing_cache"):
                self._conf_swing_cache = {}

            # helper to get swung conformers with caching keyed by (conf id, phi_deg)
            def get_swung(conf, phi_deg):
                key = (id(conf), phi_deg)
                if key in self._conf_swing_cache:
                    return self._conf_swing_cache[key]
                swung = self.conf_swing(conf, angle=phi_deg)  # keep original interface (angle param)
                self._conf_swing_cache[key] = swung
                return swung

            # search at multiple angular resolutions
            for phi_deg in (60, 15, 3, 1):
                # precompute swung conformers for both partners at this phi_deg
                new1_confs = get_swung(base_pair[0].conf, phi_deg)
                new2_confs = get_swung(base_pair[1].conf, phi_deg)

                # include the base conformers themselves
                confs1 = new1_confs + [base_pair[0].conf]
                confs2 = new2_confs + [base_pair[1].conf]

                # for each conf list, find the matching atom (by name) and collect coordinates
                entries1 = []
                for conf in confs1:
                    atom1 = next((a for a in conf.atoms if a.atomname == c1.atom.atomname), None)
                    if atom1 is not None:
                        entries1.append((conf, atom1, np.array(atom1.xyz, dtype=float)))
                entries2 = []
                for conf in confs2:
                    atom2 = next((a for a in conf.atoms if a.atomname == c2.atom.atomname), None)
                    if atom2 is not None:
                        entries2.append((conf, atom2, np.array(atom2.xyz, dtype=float)))

                if not entries1 or not entries2:
                    continue  # nothing to compare at this angle

                # build numpy arrays of coordinates
                coords1 = np.vstack([e[2] for e in entries1])  # shape (n1,3)
                coords2 = np.vstack([e[2] for e in entries2])  # shape (n2,3)

                # compute pairwise squared distances efficiently
                # (x-y)^2 = x^2 + y^2 - 2*x.dot(y)
                c1_sq = np.sum(coords1**2, axis=1)[:, None]  # (n1,1)
                c2_sq = np.sum(coords2**2, axis=1)[None, :]  # (1,n2)
                cross = coords1.dot(coords2.T)               # (n1,n2)
                d2_matrix = c1_sq + c2_sq - 2.0 * cross      # (n1,n2)

                # compute absolute difference to target squared distance
                diffs = np.abs(d2_matrix - HBOND_DISTANCE_END2)
                min_idx = np.unravel_index(np.argmin(diffs), diffs.shape)
                min_doff = float(diffs[min_idx])

                if min_doff < base_doff:
                    i, j = min_idx
                    conf1, atom1, _ = entries1[i]
                    conf2, atom2, _ = entries2[j]
                    base_doff = min_doff
                    base_pair = (Hbond_Element(atom1, conf1, c1.res), Hbond_Element(atom2, conf2, c2.res))

            # if improved at this resolution, allow further local refinement by repeating this phi loop
            # the outer for-loop already progressively refines (coarse->fine)

            # Post-filter: do not return anything if the atoms are beyond H bond distance (3.5*3.5 - 3*3)
            if base_doff > 3.25 or base_pair == (c1, c2):
                return None
            else:
                return base_pair
        

        # Collect all potential Hbond acceptor/donor atoms in the protein
        Hbond_candidates = []
        for res in self.protein.residues:
            if len(res.conformers) > 1:
                conf = res.conformers[1]
                for atom in conf.atoms:
                    if atom.element in HBOND_ATOM_ELEMENTS and atom.charge < HBOND_ATOM_CHARGE:
                        candidate = Hbond_Element(atom, conf, res)
                        Hbond_candidates.append(candidate)

        logging.info("Found %d potential hydrogen bond donors and acceptors" % len(Hbond_candidates))
        # go over all pairs to optimize each pair
        for ie1 in range(len(Hbond_candidates)-1):
            candidate1 = Hbond_candidates[ie1]
            for ie2 in range(ie1+1, len(Hbond_candidates)):
                candidate2 = Hbond_candidates[ie2]
                optimized_confs = look_for_hbond(self, candidate1, candidate2)
                if optimized_confs:
                    new_candidate1 = optimized_confs[0]
                    if new_candidate1.atom != candidate1.atom:
                        new_candidate1.conf.history = new_candidate1.conf.history[:2] + "H" + new_candidate1.conf.history[3:]
                        new_candidate1.res.conformers.append(new_candidate1.conf)
                        n_new_rotamers += 1
                    new_candidate2 = optimized_confs[1]
                    if new_candidate2.atom != candidate2.atom:
                        new_candidate2.conf.history = new_candidate2.conf.history[:2] + "H" + new_candidate2.conf.history[3:]
                        new_candidate2.res.conformers.append(new_candidate2.conf)
                        n_new_rotamers += 1

        return n_new_rotamers
    
    def repack_sidechains(self):
        """Repack side chains to optimize interactions and reduce conformers having steric clashes."""
        vdw = vdw_microstate_ir
        
        max_iterations = int(self.prm.get("MAX_ITER", "10"))  # default 10 iterations
        occ_cutoff = float(self.prm.get("REPACK_CUTOFF", "0.01"))  # default 0.01 occupancy cutoff
        repacks = int(self.prm.get("REPACKS", "500"))   # default 500 repack
        n_delete = 0

        logging.info("   Prepare vdw energy lookup table. This may take a while...")
        table = precalculate_vdw(self)  # This also updates conf.i as index in lookup table
        logging.info("   Done calculating vdw energy lookup table.")

        converged_ms = []       # stats of converged microstates

        # Collect residues with sidechains that make up the microstate. 
        # Single conformer residues are included so that energy calc is complete.
        # Backbone conformers are not included in microstate, but are included in energy calc.
        mutable_residues = [res for res in self.protein.residues if len(res.conformers) > 1]
 
        # loop over a pre-defined number of initial microstates, as in (REPACKS)
        # Precompute sidechain conformers and their indices to avoid repeated attribute lookups
        sidechain_confs = [res.conformers[1:] for res in mutable_residues]  # sidechain conformers per mutable residue
        sidechain_conf_indices = [[conf.i for conf in confs] for confs in sidechain_confs]
        n_mutable = len(mutable_residues)
        rand = random
        opt_seq = list(range(n_mutable))
        rng = np.random.default_rng()  # use numpy random generator for better performance, it uses system entropy as seed

        # Repacking main loop
        for ipack in range(repacks):            # generate a random initial state (choose one sidechain conformer per mutable residue)
            
            # --- Generate random initial microstate (much faster than list comprehension) ---
            ms = np.empty(n_mutable, dtype=np.int32)
            prev = np.empty_like(ms)
            for ires, idxs in enumerate(sidechain_conf_indices):
                ms[ires] = rng.choice(idxs)
            prev[:] = ms
            # local aliases to minimize overhead


            for istep in range(max_iterations):
                # get the random order of residues that repack will optimize
                rand.shuffle(opt_seq)

                # loop over residues to find the lowest energy conformer
                for ires in opt_seq:
                    confs = sidechain_confs[ires]
                    # only search residues with more than one sidechain conformer (same logic as original: >2 total conformers)
                    if len(confs) <= 1:
                        continue

                    # find best conformer by scanning temp vdw values (use local vars to minimize overhead)
                    best_val = 1e300  # a large number
                    best_conf_i = confs[0].i
                    for conf in confs:
                        ms[ires] = conf.i
                        val = vdw(ires, ms, table)
                        if val < best_val:
                            best_val = val
                            best_conf_i = conf.i
                    ms[ires] = best_conf_i  # set the minimum vdw conformer in microstate

                # test if the microstate has converged, quit repacking if converged
                break_step = istep + 1  # record current break step number for log
                if not np.array_equal(ms, prev):
                    prev[:] = ms
                else:
                    break
            # When exit, record the converged microstate and log the step number
            logging.debug(f"    Repack {ipack+1}/{repacks} converged at step {break_step}.")
            # Print a progress for every 10% of repacks or 50 repacks, whichever is smaller
            print_interval = max(1, min(repacks // 10, 50))
            if (ipack + 1) % print_interval == 0:
                logging.info(f"   Completed {ipack + 1} out of {repacks} repacks.")
            converged_ms.append(ms)

        # Convert converged_ms to conf_occ, and select only the conformers pass the cutoff threshold (REPACK_CUTOFF)
        # In precalculate_vdw(), conf.i is assigned as the index of the conformer in the list of conformers with atoms.
        # This ensures each conformer with atoms receives a unique index for mapping purposes.
        mapping_iconf_to_conf = {}
        for residue in self.protein.residues:
            for conf in residue.conformers[1:]:
                mapping_iconf_to_conf[conf.i] = conf 
        
        # Go over converged microstates to add conformer occurrences
        for res in self.protein.residues:
            for conf in res.conformers:
                conf.occ = 0  # reset occurrence
                conf.is_native = len(conf.history) >= 3 and conf.history[2] in HISTORY_NATIVE

        for ms in converged_ms:
            for iconf in ms:
                conf = mapping_iconf_to_conf.get(iconf, None)
                if conf is not None:
                    conf.occ += 1

        n_ms = len(converged_ms)
        for res in self.protein.residues:
            for conf in res.conformers:
                conf.occ /= n_ms

        # Recompose conformer lists based on occ_cutoff
        for res in self.protein.residues:
            filtered_confs = [res.conformers[0]]  # always keep backbone conformer
            for conf in res.conformers[1:]:  # skip backbone conformer
                if conf.occ > occ_cutoff or conf.is_native or conf.history[3] == "W":  # always native and swap conformers
                    filtered_confs.append(conf)
            n_delete += len(res.conformers) - len(filtered_confs)
            res.conformers = filtered_confs

        return n_delete
    
    def most_exposed_rotamers(self) -> int:
        """
        Generate most exposed rotamers for residues based on solvent accessible surface area (SASA).
        Residues with sidechain conformers having SASA greater than EXPOSED_CONFORMER_START are considered for generating
        most exposed rotamers. The new rotamer is created by adjusting the sidechain atoms to maximize exposure.

        Returns:
            int: The number of new most exposed rotamers generated.
        """

        n_new_rotamers = 0
        exposed_start = EXPOSED_CONFORMER_START   # Only surface residues will search more exposed, default 0.05
        step_angles = [60, 15, 3, 1]  # multi-resolution search angles

        # Necessary preparations
        self.assign_radii()        # needed for SASA calculation
        background_atoms = set()   # collect all backbone and native sidechain atoms
        for residue in self.protein.residues:
            for atom in residue.conformers[0].atoms:  # backbone is always the first conformer
                background_atoms.add(atom)
            if len(residue.conformers) > 1:
                native_conf = residue.conformers[1]
                for atom in native_conf.atoms:
                    background_atoms.add(atom)


        # Now check each residue's native conformer for 1) rotatable bonds and 2) SASA
        for residue in self.protein.residues:
            if len(residue.conformers) < 2:
                continue  # no sidechain conformer to process
            tracking_conf = residue.conformers[1]   # Start from the native sidechain conformer
            coords = np.array([atom.xyz for atom in tracking_conf.atoms])
            radii = np.array([atom.r_boundary for atom in tracking_conf.atoms])
            other_atoms = background_atoms - set(tracking_conf.atoms)
            other_coords = np.array([atom.xyz for atom in other_atoms])
            other_radii = np.array([atom.r_boundary for atom in other_atoms])
            sasa_tracking = sasa_in_context(coords, radii, other_coords, other_radii)
            most_exposed_conf = None
            if sasa_tracking < exposed_start:
                continue  # not exposed enough, skip
            for angle in step_angles:
                logging.debug(f"Residue {residue.resid} SASA {sasa_tracking:.2f} exploring angle {angle}...")
                new_confs = self.conf_swing(tracking_conf, angle=angle, heavy_atom_only=True)
                if not new_confs:
                    break   # Not rotatable, break instead of continuing
                for new_conf in new_confs:
                    coords_new = np.array([atom.xyz for atom in new_conf.atoms])
                    sasa_new = sasa_in_context(coords_new, radii, other_coords, other_radii)
                    if sasa_new > sasa_tracking:
                        new_conf.history = new_conf.history[:2] + "X" + new_conf.history[3:]
                        most_exposed_conf = new_conf
                        tracking_conf = new_conf  # continue from this new conformation
                        sasa_tracking = sasa_new  # update to the new higher SASA
                        logging.debug(f"  Found more exposed rotamer with SASA {sasa_new:.2f}")
            if most_exposed_conf is not None:
                residue.conformers.append(most_exposed_conf)
                n_new_rotamers += 1

        return n_new_rotamers
    
    def ionization_conformers(self) -> int:
        """
        Generate ionization conformers for residues that can change protonation states.
        This does not actually add protonated H atoms, but adds conformer types indicating different ionization states.
        """
        # Placeholder for future implementation
        n_new_rotamers = 0

        # Prepare a mapping of residues that can have conformer types
        # CONFLIST in ftpl is not a definitive list of conformer types because a residue may have dummy conformers.
        # A better approach is to check the CONNECT records and exclude "BK" conformers.
        valid_res_conftypes = {}  # resname -> list of non-dummy conformer types
        for key in self.tpl.keys():
            if key[0] == "CONNECT":
                confname = key[2]
                resname = confname[:3]
                conftype = confname[3:5]
                if conftype != "BK":
                    if resname not in valid_res_conftypes:
                        valid_res_conftypes[resname] = set()
                    valid_res_conftypes[resname].add(conftype)

        # Loop over residues to generate ionization conformers
        for residue in self.protein.residues:
            resname = residue.resname
            if resname not in valid_res_conftypes:
                continue  # no valid conformer types for this residue
            new_confs = []
            for conf in residue.conformers:
                if conf.conftype == "BK":
                    continue  # skip backbone conformer                    
                other_conftypes = valid_res_conftypes[resname] - {conf.conftype}
                for conftype in other_conftypes:
                    # Create a new conformer with this conftype by cloning this conformer
                    new_conf = conf.clone()
                    new_conf.conftype = conftype
                    new_conf.history = conftype + conf.history[2:]
                    new_confs.append(new_conf)
                    n_new_rotamers += 1
            residue.conformers.extend(new_confs)
        return n_new_rotamers

    def sort_conformers(self):
        """Sort conformers in each residue by their conformer type."""
        for residue in self.protein.residues:
            nature_order = [a[3:5] for a in self.tpl.get(("CONFLIST", residue.resname), [])]  # get natural order from CONFLIST
            if nature_order:
                order_map = {conftype: i for i, conftype in enumerate(nature_order)}
                residue.conformers.sort(key=lambda conf: order_map.get(conf.conftype, 9999))

    def place_hydrogens(self):
        """Place and optimize hydrogen atoms by torsion in the protein structure."""
        self.reset_connect()
        self.make_connect12()  # needed for H placement
        for residue in self.protein.residues:
            for conformer in residue.conformers:
                for atom in conformer.atoms:
                    if atom.element != " H":
                        # Check if this heavy atom has bonded H atoms and this atom's orbital type
                        key = ("CONNECT", atom.atomname, f"{residue.resname}{conformer.conftype}")
                        connect_param = self.tpl.get(key, None)
                        logging.debug(f"Atom {atom.atomname}: orbital={connect_param.orbital if connect_param else 'N/A'}, connected={connect_param.connected if connect_param else 'N/A'}")
                        missing_h_names = [n for n in connect_param.connected if is_H(n)] if connect_param else []

                        # Get unique connected heavy atoms, example: backbone CA may connect to multiple CBs
                        connected_heavy_atoms = []
                        seen_names = set()
                        for connected_atom in atom.connect12:
                            if connected_atom.element != " H" and connected_atom.atomname not in seen_names:
                                connected_heavy_atoms.append(connected_atom)
                                seen_names.add(connected_atom.atomname)
                        
                        # Decide the appropriate H placement function based on orbital type
                        if connect_param:
                            orbital = connect_param.orbital.lower()
                            if orbital == "ion":
                                continue  # skip ions
                            elif orbital == "sp3":  # The new atoms will be added to atom's parent conformer
                                place_hydrogens_sp3(atom=atom, connected_heavy_atoms=connected_heavy_atoms, missing_h_names=missing_h_names, connect_param=connect_param)
                            elif orbital == "sp2":
                                place_hydrogens_sp2(atom=atom, connected_heavy_atoms=connected_heavy_atoms, missing_h_names=missing_h_names, connect_param=connect_param)
                            elif orbital == "sp":
                                place_hydrogens_sp(atom=atom, connected_heavy_atoms=connected_heavy_atoms, missing_h_names=missing_h_names, connect_param=connect_param)
                            else:
                                logging.warning(
                                    "Unknown orbital type '%s' for atom %s in residue %s (conformer %s); skipping hydrogen placement.",
                                    connect_param.orbital,
                                    atom.atomname,
                                    residue.resname,
                                    conformer.conftype,
                                )
                            # If any hydrogens were added, update the conformer history flag as torsion optimized
                            if missing_h_names:
                                conformer.history = conformer.history[:6] + "M" + conformer.history[7:]

    def optimize_hydrogen(self):
        """
        Optimize hydrogen positions by forming hydrogen bonds where possible.
        
        Algorithm:
        1. Identify potential hydrogen donors and acceptors based on atom types and charges, their initial positions, and rotational freedom.
        2. On the H atom of each donor, perform rotational adjustments to reach optimal distance.
        """

        # Necessary preparations
        self.protein.serialize()
        self.assign_charges()
        self.reset_connect()
        self.make_connect12()  # needed for rotate

        # Create a KDTree for fast spatial searching of charged acceptor atoms
        acceptor_atoms = []
        for residue in self.protein.residues:
            for conformer in residue.conformers:
                for atom in conformer.atoms:
                    if atom.element != " H" and atom.charge <= HBOND_ATOM_CHARGE:
                        acceptor_atoms.append(atom)
        acceptor_coords = np.array([atom.xyz for atom in acceptor_atoms])
        if len(acceptor_coords) == 0:
            logging.info("No potential Hbond acceptor atoms found in the protein.")
            return 0
        acceptor_kdtree = cKDTree(acceptor_coords)

        # Collect potential Hbond donor atoms (H atoms bonded to heavy atoms and H atom is positive)
        donor_candidates = []
        for residue in self.protein.residues:
            if len(residue.conformers) < 2:
                continue  # no sidechain conformer to process
            for conformer in residue.conformers[1:]:  # skip backbone conformer
                for atom in conformer.atoms:
                    if atom.element == " H" and atom.charge >= HBOND_H_ATOM_CHARGE:
                        # Check if bonded heavy atom is a potential donor
                        # Find the heavy atom this H is bonded to
                        bonded_heavy_atoms = [a for a in atom.connect12 if a.element != " H"]
                        if not bonded_heavy_atoms:
                            continue   # no bonded heavy atom found, ignore
                        host_heavy_atom = bonded_heavy_atoms[0]  # the host atom of the H
                        # We will have to sitiation the host heavy atom as a potential donor. One is the heavy atom is alone like HOH
                        # Another is the heavy atom had sp3 orbital and is the end of a rotatable bond
                        secondary_bonded_atoms = [a for a in host_heavy_atom.connect12 if a != atom and a.element != " H"]
                        if len(secondary_bonded_atoms) == 1:
                            # Check if host heavy atom has sp3 orbital, end of rotatable bond
                            key = ("CONNECT", host_heavy_atom.atomname, f"{residue.resname}{conformer.conftype}")
                            connect_param = self.tpl.get(key, None)
                            if connect_param and connect_param.orbital.lower() == "sp3":
                                donor_candidate = {"donor_h_atom": atom,
                                                "host_heavy_atom": host_heavy_atom,
                                                "second_heavy_atom": secondary_bonded_atoms[0]}
                                donor_candidates.append(donor_candidate)
                        elif len(secondary_bonded_atoms) == 0:
                            # Host heavy atom is alone, like HOH
                            donor_candidate = {"donor_h_atom": atom,
                                            "host_heavy_atom": host_heavy_atom,
                                            "second_heavy_atom": None}
                            donor_candidates.append(donor_candidate)
    
        # From each donor candidate, optimize the H atom position by rotating around the bond
        for donor in donor_candidates:
            donor_h_atom = donor["donor_h_atom"]
            host_heavy_atom = donor["host_heavy_atom"]
            second_heavy_atom = donor["second_heavy_atom"]
            conformer = donor_h_atom.parent_conformer
            
            # Look for potential acceptor atoms, we search the atoms in the same conformer, backbone and other residues
            xyz_h = np.array(donor_h_atom.xyz)
            nearby_indices = acceptor_kdtree.query_ball_point(xyz_h, r=HBOND_H_DISTANCE_CUTOFF)
            potential_acceptors = [acceptor_atoms[i] for i in nearby_indices]
            potential_acceptors = [a for a in potential_acceptors if a.parent_conformer.parent_residue != conformer.parent_residue]  # exclude conformers in the same residue
            
            # Filter acceptors to ensure each one is unique in position xyz
            filtered_acceptors = []
            # seen_coords = []
            # tolerance = 0.001
            # for acceptor in potential_acceptors:
            #     coord_tuple = tuple(acceptor.xyz)
            #     # Check if this coordinate is already seen within tolerance
            #     is_duplicate = False
            #     for seen_coord in seen_coords:
            #         if all(abs(c1 - c2) < tolerance for c1, c2 in zip(coord_tuple, seen_coord)):
            #             is_duplicate = True
            #             break
            #     if not is_duplicate:
            #         filtered_acceptors.append(acceptor)
            #         seen_coords.append(coord_tuple)
            # Use a set of rounded coordinates for efficient duplicate detection
            seen_coords = set()
            tolerance = 0.001
            for acceptor in potential_acceptors:
                coord_tuple = tuple(acceptor.xyz)
                # Create a hashable key based on coordinates and tolerance
                rounded_coord = tuple(round(c / tolerance) for c in coord_tuple)
                if rounded_coord not in seen_coords:
                    filtered_acceptors.append(acceptor)
                    seen_coords.add(rounded_coord)
            potential_acceptors = filtered_acceptors

            logging.debug(f"Found {len(potential_acceptors)} potential acceptors for donor {donor_h_atom.atomname} in {conformer.confid}.")
            if second_heavy_atom is not None:
                rotatable_axis = (np.array(second_heavy_atom.xyz), np.array(host_heavy_atom.xyz))  # define rotatable axis
                for acceptor in potential_acceptors:
                    xyz_a = np.array(acceptor.xyz)
                    d_initial = np.linalg.norm(xyz_h - xyz_a)
                    best_d = d_initial
                    best_angle = 0
                    # Rotate H atom around the rotatable axis to find optimal position
                    for angle in range(0, 360, 5):  # rotate in 5 degree increments
                        new_xyz_h = rotate_point_around_axis(xyz_h, rotatable_axis[0], rotatable_axis[1], angle)
                        d_new = np.linalg.norm(new_xyz_h - xyz_a)
                        if abs(d_new - HBOND_H_DISTANCE_OPTIMAL) < abs(best_d - HBOND_H_DISTANCE_OPTIMAL):
                            best_d = d_new
                            best_angle = angle
                    # If best angle found improves the distance, apply the rotation
                    if best_angle != 0:
                        # collect all other atoms connected to host heavy atom to rotate together
                        connected_atoms = [atom for atom in host_heavy_atom.connect12 if atom != second_heavy_atom]
                        connected_atoms_coords = [np.array(atom.xyz) for atom in connected_atoms]
                        new_coords = swing_atoms(rotatable_axis[0], rotatable_axis[1], connected_atoms_coords, best_angle)
                        # ----------------------------------------------------------------------
                        # Verify new_coords with the donor_h_atom position, INTERNAL DEBUGGING
                        donor_h_new_xyz = rotate_point_around_axis(xyz_h, rotatable_axis[0], rotatable_axis[1], best_angle)
                        idx_h = -1
                        for i, atom in enumerate(connected_atoms):
                            if atom == donor_h_atom:
                                idx_h = i
                                break
                        if idx_h == -1:
                            connected_atoms_names = ['"' + atom.atomname + '"' for atom in connected_atoms]
                            logging.error(f"Could not find donor {donor_h_atom.atomname} in connected atoms {connected_atoms_names}.")                            
                            continue
                        else:
                            donor_hnew_xyz2 = new_coords[idx_h]
                            if not np.allclose(donor_h_new_xyz, donor_hnew_xyz2):
                                logging.error(f"Mismatch in computed new position for donor H atom {donor_h_atom.atomname} during optimization.")
                                continue
                        # ----------------------------------------------------------------------

                        # Apply new coordinates on a copy of the conformer
                        new_conformer = conformer.clone()
                        for atom, new_coord in zip(connected_atoms, new_coords):
                            # Find the corresponding atom in the new conformer
                            new_atom = next((a for a in new_conformer.atoms if a.atomname == atom.atomname), None)
                            if new_atom:
                                new_atom.xyz = list(new_coord)
                        new_conformer.history = new_conformer.history[:6] + "H" + new_conformer.history[7:]  # Optimized H bond
                        residue = conformer.parent_residue
                        residue.conformers.append(new_conformer)

                        logging.debug(f"Optimized H atom {donor_h_atom.atomname} in {conformer.confid} by rotating {best_angle} degrees.")
            else: # No rotatable bond, like HOH, point H to the acceptor directly
                for acceptor in potential_acceptors:
                    xyz_a = np.array(acceptor.xyz)
                    d_initial = np.linalg.norm(xyz_h - xyz_a)
                    direction_ha = (xyz_a - xyz_h) / d_initial  # unit vector from H to A
                    new_xyz_h = np.array(host_heavy_atom.xyz) + direction_ha * BOND_DISTANCE_H
                    d_new = np.linalg.norm(new_xyz_h - xyz_a)
                    if abs(d_new - HBOND_H_DISTANCE_OPTIMAL) < abs(d_initial - HBOND_H_DISTANCE_OPTIMAL):
                        # Obtain the actual rotation needed to move H to new_xyz_h
                        v0 = np.array(host_heavy_atom.xyz)  # The center atom is host_heavy_atom, name it v0
                        v1 = np.array(xyz_h)                # The original H position is v1 
                        v2 = np.array(new_xyz_h)            # The new H position is v2
                        a = v1 - v0
                        b = v2 - v0
                        # Create rotation using SciPy
                        rot = R.align_vectors([b], [a])[0]
                        # Get other connected atoms to rotate together
                        connected_atoms = [atom for atom in host_heavy_atom.connect12]  # all connected atoms as no second heavy atom
                        connected_atoms_coords = [np.array(atom.xyz) for atom in connected_atoms]
                        new_coords = []
                        for point in connected_atoms_coords:
                            new_coord = v0 + rot.apply(point - v0)
                            new_coords.append(new_coord)
                        # Apply new coordinates on a copy of the conformer
                        new_conformer = conformer.clone()
                        for atom, new_coord in zip(connected_atoms, new_coords):
                            # Find the corresponding atom in the new conformer
                            new_atom = next((a for a in new_conformer.atoms if a.atomname == atom.atomname), None)
                            if new_atom:
                                new_atom.xyz = list(new_coord)
                        new_conformer.history = new_conformer.history[:6] + "H" + new_conformer.history[7:]  # Optimized H bond
                        residue = conformer.parent_residue
                        residue.conformers.append(new_conformer)
                        logging.debug(
                            "Optimized H atom %s in %s by pointing directly to acceptor %s.",
                            donor_h_atom.atomname,
                            conformer.confid,
                            acceptor.atomname,
                        )

    def cluster_conformers(self) -> int:
        """
        Cluster conformers in each residue to remove similar conformers based on RMSD threshold and self energy.
        Conformers within cluster rmsd threshold are clustered together, and only the conformer with the lowest self energy is retained.
        Native conformers are always retained.

        Returns:
            int: The number of conformers removed during clustering.
        """
        self.protein.serialize()
        n_removed = 0
        rmsd_threshold = float(self.prm.get("CLUSTER_RMSD", "0.1"))   # default 0.1 Å
        if rmsd_threshold <= 0.0:
            logging.info("CLUSTER_RMSD <= 0.0, skipping clustering conformers.")
            return n_removed  # no clustering needed
        
        # Calculate self vdw energies for all conformers first
        self.calculate_selfvdw_energy()

        for residue in self.protein.residues:
            # Put conformers into groups by conformer type
            conftype_groups = {}
            for conf in residue.conformers[1:]:  # skip backbone conformer
                if conf.conftype not in conftype_groups:
                    conftype_groups[conf.conftype] = []
                conftype_groups[conf.conftype].append(conf)
            # Now cluster each conformer type group
            new_conformers = [residue.conformers[0]]  # always keep backbone conformer
            for conftype, confs in conftype_groups.items():
                # Special subgroup within conftype: native conformers
                native_confs = [conf for conf in confs if conf.is_native]
                non_native_confs = [conf for conf in confs if not conf.is_native]
                # Cluster native conformers based on RMSD; returns a list of clusters, where each cluster is a list of conformers
                if native_confs:
                    clusters = cluster_conformers_rmsd(native_confs, rmsd_threshold)
                    for cluster in clusters:
                        # Select the conformer with lowest self vdw energy
                        best_conf = min(cluster, key=lambda c: c.self_vdw_energy)
                        new_conformers.append(best_conf)
                # Now process non-native conformers
                if non_native_confs:
                    clusters = cluster_conformers_rmsd(non_native_confs, rmsd_threshold)
                    for cluster in clusters:
                        # Select the conformer with lowest self vdw energy
                        best_conf = min(cluster, key=lambda c: c.self_vdw_energy)
                        new_conformers.append(best_conf)
            n_removed += len(residue.conformers) - len(new_conformers)
            residue.conformers = new_conformers    
            
        return n_removed
    
    def calculate_selfvdw_energy(self):
        """Calculate self vdw energy for all conformers in the protein."""
        self.reset_connect()
        self.make_connect12()  # needed for VDW calculation
        self.make_connect13()
        self.make_connect14()
        self.assign_radii()  # needed for VDW calculation

        backbone_atoms = []
        for residue in self.protein.residues:
            for atom in residue.conformers[0].atoms:
                backbone_atoms.append(atom)

        # Now check each conformer, also mark the native conformers
        for residue in self.protein.residues:
            for conformer in residue.conformers[1:]:  # skip backbone conformer
                conformer.is_native = len(conformer.history) >= 3 and conformer.history[2] in HISTORY_NATIVE
                self_vdw_energy = 0.0
                if len(conformer.atoms) > 0:
                    conformer_atoms = [atom for atom in conformer.atoms]
                    # Self VDW energy vdw0
                    self_vdw_energy += 0.5 * vdw_atoms_to_atoms(conformer_atoms, conformer_atoms)  # self VDW counts each pair twice
                    # Backbone VDW energy vdw1
                    self_vdw_energy += vdw_atoms_to_atoms(conformer_atoms, backbone_atoms)
                conformer.self_vdw_energy = self_vdw_energy


def ordered_coords(conf):
    atoms = sorted(conf.atoms, key=lambda a: a.atomname)
    return np.array([a.xyz for a in atoms])

def cluster_conformers_rmsd(confs, rmsd_threshold):
    n = len(confs)
    coords = [ordered_coords(c) for c in confs]  # Sort the atom names to ensure consistent ordering
    if n > 1:
        dm = np.zeros((n, n))

        for i in range(n):
            for j in range(i+1, n):
                diff = coords[i] - coords[j]
                rmsd = np.sqrt(np.mean(np.sum(diff**2, axis=1)))
                dm[i, j] = rmsd
                dm[j, i] = rmsd
        
        dm_condensed = squareform(dm)
        Z = linkage(dm_condensed, method='average')   # 'single', 'complete', 'average'
        clusters_idx = fcluster(Z, t=rmsd_threshold, criterion='distance')
        
        clusters = {}
        for i, label in enumerate(clusters_idx):
            clusters.setdefault(label, []).append(confs[i])
        clusters = list(clusters.values())
    else:
        clusters = [confs]

    return clusters
