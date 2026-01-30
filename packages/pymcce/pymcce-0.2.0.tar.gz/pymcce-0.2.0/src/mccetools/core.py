import logging
import numpy as np


def pdb2ftpl(pdb_file: str, ignore_connect: bool = False):
    """Convert a single cofactor PDB file to an ftpl template file."""
    # Constants for composing the ftpl file
    ## Covalent radius to decide a bond. bond length: r1+r2
    radius = {
        " H": 0.25,
        " N": 0.65,
        " C": 0.70,
        " O": 0.60,
        " P": 1.00,
        " S": 1.00,
        "NA": 1.80,
        "CL": 1.00,
        "FE": 1.26,
        " X": 1.00  # default value for unknown elements
    }
    elebd_radius = {
        " N": 1.5,
        " H": 1.0,
        " C": 1.7,
        " O": 1.4,
        " P": 1.85,
        " S": 1.85,
        " X": 1.85
    }
    vdw_parm = {
        " C": (2.000, 0.150),
        " H": (1.000, 0.020),
        " O": (1.600, 0.200),
        " N": (1.750, 0.160),
        " S": (2.000, 0.200),
        " P": (2.000, 0.200),
        " X": (2.000, 0.173)
    }
    sp_orbitals = [" C", " N", " O", " P", " S"]
    sp3d2_orbitals = ["FE"]
    tolerance_scale = 1.3  # (r1+r2) * this scale gives the bond upper limit, value between 1.2 to 1.5 recommended


    # Internal representation of an atom in the PDB file
    class Atom():
        def __init__(self):
            self.name = ""
            self.serial = 0
            self.element = ""
            self.orbital = ""
            self.xyz = ()
            self.connect = []
            return

        def loadline(self, line):
            self.name = line[12:16]
            self.serial = int(line[6:11])
            self.element = line[76:78]
            self.xyz = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
            return

        def __repr__(self):
            return f"Atom(name={self.name}, serial={self.serial}, element={self.element}, orbital={self.orbital}, xyz={self.xyz}, connect={[iatom for iatom in self.connect]})"

    # Read the PDB file and parse atoms and connectivity
    atoms = {}
    resnames = []
    lines = open(pdb_file).readlines()
    for line in lines:
        if line.startswith("ATOM  ") or line.startswith("HETATM"):
            serial = int(line[6:11])
            atom = Atom()
            atom.loadline(line)
            atoms[serial] = atom  # serial number as key so that connectivity can be easily assigned
            resname = line[17:20]
            if resname not in resnames:
                resnames.append(resname)

    if len(resnames) != 1:
        raise ValueError(f"PDB file {pdb_file} contains multiple residue names: {resnames}. Please provide a PDB file with a single residue name.")

    if not ignore_connect:
        logging.info("Using connectivity from CONECT records in the PDB file.")
        count_connect = sum(1 for line in lines if line.startswith("CONECT"))
        if count_connect == 0:
            logging.warning("No CONECT records found in the PDB file. Will infer connectivity from atomic distances.")
            ignore_connect = True
        else:
            for line in lines:
                if line.startswith("CONECT"):
                    fields = line.split()
                    src = int(fields[1])
                    for tgt in fields[2:]:
                        if int(tgt) in atoms:
                            if int(tgt) not in atoms[src].connect:
                                atoms[src].connect.append(int(tgt))
                            if src not in atoms[int(tgt)].connect:
                                atoms[int(tgt)].connect.append(src)  # bidirectional
                        else:
                            logging.warning(f"Atom serial {tgt} in CONECT record not found in ATOM/HETATM records. This is normal for ligands with external connections.")

    if ignore_connect or all(len(atom.connect) == 0 for atom in atoms.values()):
        # No connectivity info, infer from distance
        logging.info("Inferring connectivity from atomic distances.")
        for i, atom1 in atoms.items():
            for j, atom2 in atoms.items():
                if i >= j:
                    continue
                if atom1.element in radius:
                    radius1 = radius[atom1.element]
                else:
                    radius1 = radius[" X"]
                if atom2.element in radius:
                    radius2 = radius[atom2.element]
                else:
                    radius2 = radius[" X"]

                dist = np.linalg.norm(np.array(atom1.xyz) - np.array(atom2.xyz))
                cutoff = (radius1 + radius2) * tolerance_scale
                if dist <= cutoff:
                    atom1.connect.append(j)
                    atom2.connect.append(i)  # bidirectional            
    
    # Assign orbitals based on element and connectivity
    for atom in atoms.values():
        if atom.element == " H":
            atom.orbital = "s"
        elif atom.element in sp_orbitals:
            if len(atom.connect) == 4:
                atom.orbital = "sp3"
            elif len(atom.connect) == 3 or len(atom.connect) == 2:  # need to check bond angles to differentiate sp3, sp2 and sp
                bond1 = atoms[atom.connect[0]].xyz - np.array(atom.xyz)
                bond2 = atoms[atom.connect[1]].xyz - np.array(atom.xyz)
                angle = np.arccos(np.dot(bond1, bond2) / (np.linalg.norm(bond1) * np.linalg.norm(bond2))) * 180.0 / np.pi
                angle_diffs = {109.5: abs(angle - 109.5), 120.0: abs(angle - 120.0), 180.0: abs(angle - 180.0)}
                closest_angle = min(angle_diffs, key=angle_diffs.get)
                if angle_diffs[closest_angle] < 15:
                    if closest_angle == 109.5:
                        atom.orbital = "sp3"
                    elif closest_angle == 120.0:
                        atom.orbital = "sp2"
                    elif closest_angle == 180.0:
                        atom.orbital = "sp"
                else:
                    atom.orbital = "udf"
                    logging.warning(f"Atom {atom.name} ({atom.element}) has an unusual bond angle of {angle:.2f} degrees.")

            elif len(atom.connect) == 1:
                # doesn't matter in terms of geometry, usually sp3 but O on CH3-(CO)-CH3 is sp2 instead of sp3.
                atom.orbital = "sp3"
            elif len(atom.connect) == 0:
                atom.orbital = "ion"
            else:
                atom.orbital = "udf"
        elif atom.element in sp3d2_orbitals:
            if len(atom.connect) >= 4:  # usually 5 or 6 for Fe in heme
                atom.orbital = "sp3d2"
            elif len(atom.connect) == 0:
                atom.orbital = "ion"
            else:
                atom.orbital = "udf"
        else:
            logging.warning(f"Atom {atom.name} ({atom.element}) has {len(atom.connect)} connections, which is unusual. Assigning orbital as 's'.")
            atom.orbital = "udf"

    # Write the ftpl file
    ftpl_file = pdb_file.rsplit(".", 1)[0] + ".ftpl"
    with open(ftpl_file, "w") as fout:    
        # CONFLIST
        fout.write("# Conformer definition\n")
        fout.write(f"CONFLIST, {resnames[0]}: {resnames[0]}BK, {resnames[0]}01\n\n")  # Always have a backbone conformer, even if 0 atoms

        # CONNECT
        fout.write("# Atom connectivity - name and bonds\n")
        for atom in atoms.values():
            connect_str = ",".join([f"\"{atoms[i].name}\"" for i in atom.connect])
            fout.write(f"CONNECT, \"{atom.name}\", {resnames[0]}01: {atom.orbital:>6s}, {connect_str}\n")

        # Charge
        fout.write("\n# Atom charges\n")
        for atom in atoms.values():
            fout.write(f"CHARGE, {resnames[0]}01, \"{atom.name}\": to be determined\n")

        # Radius
        fout.write("\n# Atom radii: dielectric boundary radius, VDW radius, and energy well depth\n")
        for atom in atoms.values():
            if atom.element not in elebd_radius:
                bnd_radius = elebd_radius[" X"]
                vdw_radius = vdw_parm[" X"][0]
                energy_well_depth = vdw_parm[" X"][1]
            else:
                bnd_radius = elebd_radius[atom.element]
                vdw_radius = vdw_parm[atom.element][0]
                energy_well_depth = vdw_parm[atom.element][1]
            fout.write(f"RADIUS, {resnames[0]}01, \"{atom.name}\": {bnd_radius:6.3f}, {vdw_radius:6.3f}, {energy_well_depth:6.3f}\n")

        # Conformer properties that appear in head3.lst
        fout.write("\n# Conformer properties that appear in head3.lst\n")
        fout.write(f"CONFORMER, {resnames[0]}01: Em0=0.0, pKa0=0.0, ne=0, nH=0\n")


    # Summarize the output
    print("\nSummary:")
    print(f"FTPL file written to {ftpl_file}. Please review and edit the following fields as needed:")
    print("- Conformer list: CONFLIST")
    print("- Atom connectivity: CONNECT")
    print("- Atom charges: CHARGE")
    print("- Atom radii: RADIUS")
    print("- Conformer properties: CONFORMER")
