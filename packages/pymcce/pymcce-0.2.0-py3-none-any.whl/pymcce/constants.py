import numpy as np

"""
Shared constants for PyMCCE modules.
"""
USER_FTPL = "user_ftpl"         # default folder for user provided ftpl files
FTPL_DUMP = "record.tpl"        # default output tpl file for dumping ftpl
PREPROCESS_PRM_DUMP = "preprocess.prm"  # default output prm file for dumping used parameters in preprocessing
CONFORMERS_PRM_DUMP = "conformers.prm"  # default output prm file for dumping used parameters in conformer generation
HEAD1_LST = "head1.lst"         # default output head1.lst file for residue properties
STEP1_OUT = "step1_out.pdb"     # default output pdb file for preprocessed structure
STEP2_OUT = "step2_out.pdb"     # default output pdb file for step2 structure
ROT_STAT = "rot_stat"           # default output rotamer statistics file
CONNECT_TABLE = "connectivity.tbl"  # default output connectivity table file
ROTAMER_LEVEL1_PRM = "rotamer_level1.prm"  # prm file for rotamer level 1 (simplest)
ROTAMER_LEVEL2_PRM = "rotamer_level2.prm"  # prm file for rotamer level 2 (limited rotamers)
ROTAMER_LEVEL3_PRM = "rotamer_level3.prm"  # prm file for rotamer level 3 (extensive rotamers)
HISTORY_NATIVE = ['O', 'A', 'B', 'C', 'D', 'W'] # history codes (3rd char in history string) indicating native conformers

# This is for detecting altloc on backbone atoms
# A backbone atom should have residue name AND name match the following to be considered as backbone
BACKBONE_ATOMS = {" N  ", " CA ", " C  ", " O  "}
RESIDUE_NAMES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "CYD", "GLN", "GLU", "GLY",
    "HIL", "HIS", "ILE", "LEU", "LYS", "MEL", "MET", "PHE", "PRO",
    "SER", "THR", "TRP", "TYR", "VAL"
}

# Precompute sphere points once, for SAS calculation
N_POINTS = 122

def generate_sphere_points(n_points):
    phi = (1 + np.sqrt(5)) / 2
    indices = np.arange(n_points)
    z = 1 - (2 * indices + 1) / n_points
    theta = 2 * np.pi * indices / phi
    x = np.sqrt(1 - z ** 2) * np.cos(theta)
    y = np.sqrt(1 - z ** 2) * np.sin(theta)
    return np.stack((x, y, z), axis=1)

SPHERE_POINTS = generate_sphere_points(N_POINTS)

# SAS constants, also used by MCCE class to detect connected atoms
SAS_PROBE_RADIUS = 1.4  # in Angstrom
ATOM_RADII = {
    " H": 1.20,  # Hydrogen
    " C": 1.70,  # Carbon
    " N": 1.55,  # Nitrogen
    " O": 1.52,  # Oxygen
    " S": 1.80,  # Sulfur
    " P": 1.80,  # Phosphorus
}
ATOM_RADIUS_UNKNOWN = 1.80  # Default radius for unknown elements


# RADII defaults
# RADIUS, ALABK, " N  ": 1.500, 1.824, 0.170
# RADIUS, ALABK, " H  ": 1.000, 0.600, 0.016
# RADIUS, ALABK, " CA ": 2.000, 1.908, 0.109
# RADIUS, ALABK, " HA ": 0.000, 1.387, 0.016
# RADIUS, ALABK, " C  ": 1.700, 1.908, 0.086
# RADIUS, ALABK, " O  ": 1.400, 1.661, 0.210
# RADIUS, ALA01, " CB ": 2.000, 1.908, 0.109
# RADIUS, ALA01, " HB1": 0.000, 1.487, 0.016
# RADIUS, ALA01, " HB2": 0.000, 1.487, 0.016
# RADIUS, ALA01, " HB3": 0.000, 1.487, 0.016
ATOM_RADII_VDW_DEFAULT = {
    " N": (1.50, 1.824, 0.170),
    " H": (1.00, 0.600, 0.016),
    " C": (2.00, 1.908, 0.109),
    " O": (1.40, 1.661, 0.210),
    " S": (1.850, 2.000, 0.250),
}
ATOM_RADII_VDW_DEFAULT_UNKNOWN = (1.80, 2.000, 0.200)  # Default VDW radii for unknown elements



# Loose cofactors that can be stripped off if exposed to solvent
# LOOSE_COFACTORS = ["HOH", "NO3", "NA ", "CL ", "PO4"] -> Now in ftpl file loose_cofactors.ftpl so users can modify


# Standard and extended amino acid names for identify terminal residues
TERMINAL_RESIDUES = {"NTR", "NTG", "CTR"}
AMINO_ACIDS = {"ALA", "ARG", "ASN", "ASP", "CYS", "CYD", "CYL", "GLN", "GLU", "GLY",
               "HIL", "HIS", "ILE", "LEU", "LYS", "MET", "MEL", "PHE", "PRO",
               "SER", "THR", "TRP", "TYR", "VAL"}
NTR_ATOMS = {" N  ", " CA "}  # heavy atoms only
CTR_ATOMS = {" C  ", " O  ", " OXT"}  # heavy atoms only
SPECIAL_LIGAND_RESIDUES = {"CYL"}  # The ligands in this set connect to an atom without predefined mutual connections

# HBond directed rotamer generation constants
HBOND_ATOM_ELEMENTS = {" O", " N", " F"}  # Hbond atoms need to have this element
HBOND_ATOM_CHARGE = -0.2  # Hbond atoms need to have charge more negative than this
HBOND_DISTANCE_INI2 = 10.0 * 10.0  # Optimize if the initial distance is within this distance, squared
HBOND_DISTANCE_END2 = 3.0 * 3.0  # Make the final distance as close as possible to this distance, squared
HBOND_H_ATOM_CHARGE = 0.2 # Hbond donor H atom needs to have charge more positive than this
HBOND_H_DISTANCE_CUTOFF = 2.5  # Only consider Hbond if the H-acceptor distance from H can be within this distance
HBOND_H_DISTANCE_OPTIMAL = 1.0 # Try to optimize H-acceptor distance from H to this distance

# Most exposed rotamer generation constants
EXPOSED_CONFORMER_START = 0.05  # Surface exposure in ratio to start making exposed rotamers

# Bond distance for adding H atoms
BOND_DISTANCE_H = 1.2  # in Angstrom

# Atom masses (in atomic mass unit)
ATOM_MASSES = { " H" : 1,
                " C" : 12,
                " N" : 14,
                " O" : 16,
                " S" : 32,
                " P" : 31,
                " F" : 19,
                "CL": 35.5,
                "BR": 80,
                "I" : 127,
                "ZN": 65,
                "CA": 40,
                "MG": 24,
                "MN": 55,
                "FE": 56,
                "CU": 63,
                "CO": 59,
                "NI": 59,
                " B": 10,
                "SI": 28,
                "LI": 7,
                "BE": 9,
                "NA": 23,
                "AL": 27,
                " K": 39}
