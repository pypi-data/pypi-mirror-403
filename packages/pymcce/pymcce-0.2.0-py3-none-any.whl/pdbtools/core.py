import logging
from pathlib import Path
import requests
import sys
from collections import defaultdict
import re
from pymcce.constants import RESIDUE_NAMES
from pymcce.mcce import default_ftpl_folder, default_ideal_structures_folder, is_H
import numpy as np
from pymcce.utils import Transformation


# Basic ANSI color codes
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"


def getpdb(pdb_name: str):
    """Download a PDB file from the Protein Data Bank."""
    url = f"https://files.rcsb.org/download/{pdb_name}.pdb"
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error while downloading {pdb_name}.pdb: {e}")
        return
    if response.status_code == 200:
        with open(f"{pdb_name}.pdb", "wb") as f:
            f.write(response.content)
        logging.info(f"Downloaded {pdb_name}.pdb")
    else:
        logging.error(f"Failed to download {pdb_name}.pdb")


def split_models(pdb_file: str):
    """Split a PDB file into separate models."""
    logging.info(f"Splitting models in {pdb_file}")
    try:
        with open(pdb_file, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.error(f"PDB file {pdb_file} not found.")
        return

    models = []
    current_model = []
    inside_model = False

    for line in lines:
        if line.startswith("MODEL"):
            inside_model = True
            current_model = []
        elif line.startswith("ENDMDL"):
            if inside_model and current_model:
                models.append(current_model)
            inside_model = False
        elif inside_model:
            current_model.append(line)

    # Handle case where no models were found
    if not models:
        if lines:
            logging.warning(f"No MODEL/ENDMDL records found in {pdb_file}. Skipping.")
        else:
            logging.warning(f"No models found in {pdb_file} (file is empty).")
        return

    for i, model in enumerate(models, start=1):
        model_file = f"{pdb_file.rsplit('.', 1)[0]}_model_{i}.pdb"
        with open(model_file, "w") as mf:
            mf.writelines(model)
        logging.info(f"Wrote model {i} to {model_file}")


def split_altlocs(pdb_file: str):
    """Split a PDB file into separate alternate locations."""
    logging.info(f"Splitting alternate locations in {pdb_file} if that happens on the backbone atoms")
    try:
        with open(pdb_file, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.error(f"PDB file {pdb_file} not found.")
        return

    BACKBONE_ATOMS = {" N  ", " CA ", " C  ", " O  "}
    AMINO_ACIDS = {"ALA", "ARG", "ASN", "ASP", "CYS", "CYD", "CYL", "GLN", "GLU", "GLY",
               "HIL", "HIS", "ILE", "LEU", "LYS", "MET", "MEL", "PHE", "PRO",
               "SER", "THR", "TRP", "TYR", "VAL"}

    # Logic:
    # Initial scan of all atoms to see if there are any altlocs on backbone atoms of standard amino acids.
    # If yes, then need to split into separate files, otherwise do nothing
    # First, organize atoms into residues, using residue name, chain ID, and residue sequence number and insertion code as the key.
    # Within each residue, divide atoms into common atoms (no altloc) and altloc groups.
    # Combine common atoms with altloc group atoms. They are the residues to be written to separate files.
    all_altlocs = set()
    residues = {}
    for line in lines:
        if line.startswith(("ATOM", "HETATM")):
            res_name = line[17:20]
            chain_id = line[21]
            res_seq = line[22:26]
            ins_code = line[26]
            alt_loc = line[16].strip()  # Alt loc indicator, can be blank

            res_key = (res_name, chain_id, res_seq, ins_code)
            if res_key not in residues:
                residues[res_key] = {"common": [], "altlocs": {}}

            if alt_loc == "":
                residues[res_key]["common"].append(line)
            else:
                all_altlocs.add(alt_loc)
                if alt_loc not in residues[res_key]["altlocs"]:
                    residues[res_key]["altlocs"][alt_loc] = []
                residues[res_key]["altlocs"][alt_loc].append(line)
    
    # Check if any backbone atoms have altlocs in standard amino acids
    need_split = False
    for (res_name, _, _, _), atom_groups in residues.items():
        if res_name in AMINO_ACIDS:
            for alt_loc, atoms in atom_groups["altlocs"].items():
                for atom in atoms:
                    atom_name = atom[12:16]
                    if atom_name in BACKBONE_ATOMS:
                        need_split = True
                        break
                if need_split:
                    break
        if need_split:
            break
    if not need_split:
        logging.info(f"No altlocs on backbone atoms found. No splitting needed.")
        return

    # Now, allocate the lines into separate files for each altloc combination
    altloc_files = {alt_loc: [] for alt_loc in all_altlocs}
    for (res_name, chain_id, res_seq, ins_code), atom_groups in residues.items():
        common_atoms = atom_groups["common"]
        altloc_atoms = atom_groups["altlocs"]
        if not altloc_atoms:
            # No altlocs in this residue, add common atoms to all files
            for alt_loc in altloc_files:
                altloc_files[alt_loc].extend(common_atoms)
        else:
            for alt_loc, atoms in altloc_atoms.items():
                altloc_files[alt_loc].extend(common_atoms + atoms)

    for alt_loc in sorted(altloc_files.keys()):
        atom_lines = altloc_files[alt_loc]
        altloc_file = f"{pdb_file.rsplit('.', 1)[0]}_altloc_{alt_loc}.pdb"
        with open(altloc_file, "w") as af:
            af.writelines(atom_lines)
        logging.info(f"Wrote altloc {alt_loc} to {altloc_file}")


def print_summary(messages):
    """Print summary messages at the end."""
    # Output all messages
    sys.stdout.writelines(messages)
    sys.stdout.flush()

def check_missing_sidechain_heavy_atoms(lines):
    """Check for missing side chain heavy atoms in known residues and cofactors."""
    missing_sidechain_atoms = {}   # (chain_id, seq_num, ins_code, res_name) -> missing_atoms
    # Convert lines into residues
    residues = {}
    for line in lines:
        if line.startswith(("ATOM  ")):
            res_name = line[17:20]
            chain_id = line[21]
            seq_num = line[22:26]
            ins_code = line[26]
            atom_name = line[12:16]
            if res_name in RESIDUE_NAMES:
                residues_key = (chain_id, seq_num, ins_code, res_name)
                if residues_key not in residues:
                    residues[residues_key] = set()
                residues[residues_key].add(atom_name)
    # Get expected side chain atoms from ftpl files
    ftpl_folder = default_ftpl_folder()
    expected_sidechain_atoms = {}
    for ftpl_file in Path(ftpl_folder).glob("*.ftpl"):
        with open(ftpl_file) as f:
            for line in f:
                if line.startswith("CONNECT"):
                    parts = line.split(":")
                    key_parts = parts[0].split(",")
                    coformername = key_parts[2].strip()
                    if coformername.endswith("BK"):
                        continue  # skip backbone conformer
                    res_name = key_parts[2].strip()[:3].strip(" _")  # take residue name from conformer name in ftpl
                    atom_name = key_parts[1].strip().strip("\"")
                    if is_H(atom_name):
                        continue  # skip hydrogens
                    if res_name not in expected_sidechain_atoms:
                        expected_sidechain_atoms[res_name] = set()
                    expected_sidechain_atoms[res_name].add(atom_name)
    # Check each residue to see if any heavy atoms are missing
    residue_keys_list = list(residues.keys())
    for residue_key in residue_keys_list:
        chain_id, seq_num, ins_code, res_name = residue_key
        present_atoms = residues[residue_key]
        if res_name in expected_sidechain_atoms:
            missing_atoms = expected_sidechain_atoms[res_name] - present_atoms
            if missing_atoms:
                missing_sidechain_atoms[residue_key] = missing_atoms

    return missing_sidechain_atoms


def mcce_readiness(pdb_file: str):
    """
    Check if a PDB file is ready for MCCE processing.
    1. Are there multiple biounits?
    2. Are there any missing backbone atoms in standard amino acids?
    3. Are there any altlocs on backbone atoms of standard amino acids?
    4. Are there any non-standard residues?
    5. Are there any missing side chain heavy atoms?
    6. Are there multiple NMR models?
    """
    logging.info(f"Checking MCCE readiness for {pdb_file}")

    messages = ["\n" + "="*50 + "\nMCCE Readiness Check Summary:\n"]  # Collect messages to report at the end

    try:
        with open(pdb_file, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.error(f"PDB file {pdb_file} not found.")
        messages.append(f"Error: PDB file \"{pdb_file}\" not found.\n")
        return messages

    # 0. Get the summary of the protein by the REMARK lines
    info = {
        "molecule_name": None,
        "title": None,
        "method": None,
        "resolution": None,
        "biomolecules": defaultdict(list),  # {biomol_id: [chains]}
        "nmr_models": [],
        "missing_residues": [],
        "missing_atoms": []
    }

    biomol_id = None
    for line in lines:
        # --- Molecule name ---
        if line.startswith("COMPND") and "MOL_ID" in line:
            m = re.search(r"MOL_ID:\s*(\d+)", line)
            if m:
                biomol_id = m.group(1)

        elif line.startswith("COMPND") and "MOLECULE:" in line:
            molname = line.split("MOLECULE:")[-1].strip().rstrip(";")
            info["molecule_name"] = molname

        # --- Title ---
        elif "TITLE" in line:
            title = line.split("TITLE")[-1].strip()
            if info["title"]:
                info["title"] += " " + title
            else:
                info["title"] = title

        # --- Method and Resolution ---
        elif line.startswith("EXPDTA"):
            method = line.split("EXPDTA")[-1].strip()
            info["method"] = method
        elif line.startswith("REMARK") and "RESOLUTION." in line:
            m = re.search(r"([\d.]+)\s+ANGSTROMS", line)
            if m:
                info["resolution"] = float(m.group(1))

        # --- Biomolecule and Biounit Assembly ---
        elif line.startswith("REMARK 350") and "BIOMOLECULE:" in line:
            biomol_id = line.split(":")[-1].strip()
        elif line.startswith("REMARK 350") and "CHAINS:" in line and biomol_id:
            chains = line.split("CHAINS:")[-1].replace(";", "").strip()
            chain_list = [c.strip() for c in chains.split(",")]
            info["biomolecules"][biomol_id].extend(chain_list)

        # --- NMR Models ---
        elif line.startswith("MODEL "):
            model = line.split("MODEL ")[-1].strip()
            info["nmr_models"].append(model)

        # --- Missing Residues ---
        elif line.startswith("REMARK 465"):
            if "M RES" not in line:  # skip header line
                info["missing_residues"].append(line.strip())

        # --- Missing Atoms ---
        elif line.startswith("REMARK 470"):
            if "M ATOM" not in line:  # skip header line
                info["missing_atoms"].append(line.strip())

    # Output the summary info
    messages.append(f"{'-'*50}\n")
    messages.append(f"Summary based on PDB header lines\n{'-'*50}\n")
    if info["molecule_name"]:
        messages.append(f"Molecule name     : {info['molecule_name']}\n")
    if info["title"]:
        messages.append(f"Title             : {info['title']}\n")
    if info["method"]:
        messages.append(f"Method            : {info['method']}\n")
    if info["resolution"]:
        messages.append(f"Resolution (Å)    : {info['resolution']}\n")
    if info["nmr_models"]:
        messages.append(f"NMR Models        : {', '.join(info['nmr_models'])}\n")

    if info["biomolecules"]:
        messages.append("Biological Assemblies:\n")
        for bm_id, chains in info["biomolecules"].items():
            messages.append(f"  Biomolecule {bm_id}: Chains {', '.join(chains)}\n")

    if info["missing_residues"]:
        messages.append(f"\nMissing Residues ({len(info['missing_residues'])}):\n")
        for res in info["missing_residues"]:
            messages.append(f"  {res}\n")

    if info["missing_atoms"]:
        messages.append(f"\nMissing Atoms ({len(info['missing_atoms'])}):\n")
        for atm in info["missing_atoms"]:
            messages.append(f"  {atm}\n")


    messages.append(f"\n{'-'*50}\n")
    messages.append(f"Summary based on atom records (ATOM/HETATM):\n")
    messages.append(f"{'-'*50}\n")
    

    # Now perform the checks based on ATOM/HETATM records
    # 1. Check for multiple biounits in the file
    messages.append("Checking for multiple biounits based on chain IDs...\n")
    chains_withresidues = set()
    for line in lines:
        if line.startswith(("ATOM", "HETATM")):
            res_name = line[17:20]
            chain_id = line[21]
            if res_name in RESIDUE_NAMES:
                chains_withresidues.add(chain_id)
    if len(chains_withresidues) > 1:
        # Check if these chains correspond to different biounits
        biounit_chains = set()
        for chains in info["biomolecules"].values():
            biounit_chains.update(chains)
        sorted_chains = sorted(biounit_chains)
        
        if len(biounit_chains) == 0:  # No biounit info available
            messages.append(f"  {YELLOW}Warning:{RESET} No biounit information found in PDB header.\n")
            messages.append(f"           Please make sure a single biounit is used for MCCE processing.\n")
        else:
            if len(biounit_chains.intersection(chains_withresidues)) > 1:
                messages.append(f"  {YELLOW}Warning:{RESET} Multiple biounits detected involving chains: {', '.join(sorted_chains)}\n")
                messages.append("           Consider extracting a single biounit for MCCE processing.\n")
            else:
                messages.append(f"  {GREEN}Passed:{RESET} All chains belong to a single biounit.\n")
    else:
        messages.append(f"  {GREEN}Passed:{RESET} Only one chain with residues detected.\n")

    # 2. Check for missing backbone atoms in standard amino acids
    messages.append("\nChecking for missing backbone atoms in standard amino acids...\n")
    backbone_atoms = {" N  ", " CA ", " C  ", " O  "}
    residues = {}
    for line in lines:
        if line.startswith(("ATOM  ")):
            res_name = line[17:20]
            chain_id = line[21]
            seq_num = line[22:26]
            ins_code = line[26]
            if line[12:16] in backbone_atoms:
                residues_key = (chain_id, seq_num, ins_code, res_name)
                if residues_key not in residues:
                    residues[residues_key] = set()
                residues[residues_key].add(line[12:16])
    missing_backbone = []
    for (chain_id, seq_num, ins_code, res_name), atoms in sorted(residues.items()):
        if res_name in RESIDUE_NAMES:
            missing = backbone_atoms - atoms
            if missing:
                missing_backbone.append((chain_id, seq_num, ins_code, res_name, missing))
    if missing_backbone:
        for chain_id, seq_num, ins_code, res_name, missing in missing_backbone:
            messages.append(f"  {YELLOW}Warning:{RESET} Residue {res_name}{seq_num.strip()}{ins_code.strip()} in chain {chain_id} is missing backbone atoms: {', '.join(missing)}\n")
        messages.append("           Consider using 3rd party tools to add missing backbone atoms before MCCE processing.\n")
    else:
        messages.append(f"  {GREEN}Passed:{RESET} No missing backbone atoms in standard amino acids.\n")

    # 3. Check for altlocs on backbone atoms of standard amino acids
    messages.append("\nChecking for alternate locations on backbone atoms of standard amino acids...\n")
    altlocs_on_backbone = []
    for line in lines:
        if line.startswith(("ATOM  ")):
            res_name = line[17:20]
            chain_id = line[21]
            seq_num = line[22:26]
            ins_code = line[26]
            alt_loc = line[16].strip()
            atom_name = line[12:16]
            if alt_loc != "" and atom_name in backbone_atoms and res_name in RESIDUE_NAMES:
                altlocs_on_backbone.append((chain_id, seq_num, ins_code, res_name, atom_name, alt_loc))
    # Get unique chain IDs that have altlocs on backbone atoms
    unique_altlocs = sorted({alt_loc for _, _, _, _, _, alt_loc in altlocs_on_backbone})
    if len(unique_altlocs) > 1:  # Allow one altloc on backbone on top of the default blank (common atoms are fine)
        for chain_id, seq_num, ins_code, res_name, atom_name, alt_loc in altlocs_on_backbone[:10]:  # Limit to first 10 messages
            messages.append(f"  {YELLOW}Warning:{RESET} Residue {res_name}{seq_num.strip()}{ins_code.strip()} in chain {chain_id} has alternate location '{alt_loc}' on backbone atom {atom_name}\n")
        if len(altlocs_on_backbone) > 10:
            messages.append(f"           ... and {len(altlocs_on_backbone) - 10} more instances.\n")
        messages.append("           Split structure based altloc using 'pdbtools split-altlocs' before MCCE processing.\n")
    else:
        messages.append(f"  {GREEN}Passed:{RESET} No or only one alternate location on backbone atoms of standard amino acids.\n")

    # 4. Check for non-standard residues
    messages.append("\nChecking for non-standard residues...\n")
    # Get the mcce default ftpl folder and read all ftpl files to get known residues
    ftpl_folder = default_ftpl_folder()
    known_residues = set()
    for ftpl_file in Path(ftpl_folder).glob("*.ftpl"):
        with open(ftpl_file) as f:
            for line in f:
                if line.startswith("CONFLIST"):
                    parts = line.split(":")
                    known_residues.add(parts[0].split(",")[1].strip(" _"))  # strip off spaces and underscores from residue name in ftpl

    nonstandard_residues = set()
    for line in lines:
        if line.startswith(("ATOM", "HETATM")):
            res_name = line[17:20].strip()
            if res_name not in known_residues:
                nonstandard_residues.add(res_name)
    if nonstandard_residues:
        for res_name in sorted(nonstandard_residues):
            messages.append(f"  {YELLOW}Warning:{RESET} Unknown cofactor detected: {res_name}\n")
        messages.append("           MCCE treats unknown cofactors as 0-charge atoms unless ftpl files are provided.\n")
        messages.append("           Refer to the MCCE documentation for details.\n")
    else:
        messages.append(f"  {GREEN}Passed:{RESET} No non-standard residues detected.\n")

    # 5. Check for missing side chain heavy atoms
    messages.append("\nChecking for missing side chain heavy atoms...\n")
    missing_sidechain_atoms = check_missing_sidechain_heavy_atoms(lines)
    if missing_sidechain_atoms:
        for residue_key, missing in missing_sidechain_atoms.items():
            chain_id, seq_num, ins_code, res_name = residue_key
            messages.append(f"  {YELLOW}Warning:{RESET} Residue {res_name}{seq_num.strip()}{ins_code.strip()} in chain {chain_id} is missing side chain heavy atoms: {', '.join(missing)}\n")
        messages.append("           Use 'pdbtools complete-sidechain' to add missing side chain atoms before MCCE processing.\n")
    else:
        messages.append(f"  {GREEN}Passed:{RESET} No missing side chain heavy atoms in known residues and cofactors.\n")

    # 6. Check for multiple NMR models
    messages.append("\nChecking for multiple NMR models...\n")
    if len(info["nmr_models"]) > 1:
        messages.append(f"  {YELLOW}Warning:{RESET} Multiple NMR models detected: {', '.join(info['nmr_models'])}\n")
        messages.append("           Split NMR models using `pdbtools split-models` and select a single model for MCCE processing.\n")
    else:
        messages.append(f"  {GREEN}Passed:{RESET} Single NMR model or no NMR models detected.\n")
        
    return messages

def complete_sidechain(pdb_file: str, optimize: bool = False):
    """
    Complete side chain atoms in a PDB file.
    This function only completes side chain heavy atoms by aligning a template to the backbone atoms.
    Another function place_terminal_atoms() in MCCE class is provided to add missing terminal atoms (e.g., OXT and H).
    Args:
        pdb_file (str): Path to the PDB file.
        optimize (bool): Whether to optimize the side chain conformation after completion.
    """
    backbone_atoms = {" N  ", " CA ", " C  ", " O  "}

    class Missing_Residue:
        def __init__(self):
            """Class to hold information about a residue with missing side chain atoms."""
            self.key = None
            self.backbone_coords = {}
            self.backbone_lines = []
            self.sidechain_lines = []

        def complete_lines(self, ideal_structures_coords, residues):
            """Complete the residue lines by replacing side chain atoms with ideal structure."""
            # 1. Get the backbone atom coordinates from the original structure
            residue_lines = []
            ca_original_coord = self.backbone_coords.get(" CA ")
            n_original_coord = self.backbone_coords.get(" N  ")
            c_original_coord = self.backbone_coords.get(" C  ")
            if ca_original_coord is None or n_original_coord is None or c_original_coord is None:
                logging.warning(f"Cannot complete side chain for residue {self.key} due to missing backbone atoms.")
                residue_lines.extend(self.backbone_lines)  # write back original lines
                residue_lines.extend(self.sidechain_lines) # write back original side chain lines
            else:
                # 2. Get the ideal structure coordinates for that residue
                ideal_coords = ideal_structures_coords.get(self.key[3])  # res_name
                if ideal_coords is None:
                    logging.warning(f"No ideal structure found for residue {self.key[3]}. Cannot complete side chain.")
                    residue_lines.extend(self.backbone_lines)  # write back original lines
                    residue_lines.extend(self.sidechain_lines) # write back original side chain lines
                else:
                    ca_ideal_coord = ideal_coords.get(" CA ")
                    n_ideal_coord = ideal_coords.get(" N  ")
                    c_ideal_coord = ideal_coords.get(" C  ")
                    if ca_ideal_coord is None or n_ideal_coord is None or c_ideal_coord is None:
                        logging.warning(f"Ideal structure for residue {self.key[3]} missing backbone atoms. Cannot complete side chain.")
                        residue_lines.extend(self.backbone_lines)  # write back original lines
                        residue_lines.extend(self.sidechain_lines) # write back original side chain lines
                    else:
                        # 3. Align the ideal structure to the backbone N-CA-C atoms
                        # Compute rotation and translation using Kabsch algorithm
                        T = Transformation.geom_3v_onto_3v(ca_ideal_coord, n_ideal_coord, c_ideal_coord,
                                                            ca_original_coord, n_original_coord, c_original_coord)
                        # 4. Replace the side chain atoms in the original structure with the aligned ideal structure
                        residue_lines.extend(self.backbone_lines)  # write back backbone lines
                        new_sidechain_lines = []
                        for atom_name_ideal, coord_ideal in ideal_coords.items():
                            if atom_name_ideal in backbone_atoms or is_H(atom_name_ideal) or atom_name_ideal == " OXT":
                                continue  # skip backbone, H, and OXT atoms
                            # Transform the ideal side chain atom coordinate
                            coord_transformed = T.apply([coord_ideal])[0]      # Only one coordinate
                            # Create new PDB line for this atom
                            original_line = residues[self.key].get(atom_name_ideal)
                            if original_line is not None:
                                new_line = list(original_line)
                                new_line[30:54] = list(f"{coord_transformed[0]:8.3f}{coord_transformed[1]:8.3f}{coord_transformed[2]:8.3f}")
                                new_sidechain_lines.append("".join(new_line))
                            else:
                                # Atom not originally present, create a new line
                                new_line = f"ATOM  {0:5d} {atom_name_ideal} {self.key[3]} {self.key[0]}{self.key[1]}{self.key[2]}   {coord_transformed[0]:8.3f}{coord_transformed[1]:8.3f}{coord_transformed[2]:8.3f}\n"
                                new_sidechain_lines.append(new_line)
                        residue_lines.extend(new_sidechain_lines)
                        logging.info(f"Completed side chain for residue {self.key}")
            return residue_lines


    def line_indexed_by_atom(line):
        """
        Get a unique index for an atom line based on chain ID, residue sequence number, insertion code, residue name, and atom name.
        """
        chain_id = line[21]
        seq_num = line[22:26]
        ins_code = line[26]
        res_name = line[17:20]
        atom_name = line[12:16]
        residue_key = (chain_id, seq_num, ins_code, res_name)
        return (residue_key, atom_name)


    # Check which residues are missing side chain heavy atoms
    lines = open(pdb_file).readlines()
    missing_sidechain_atoms = check_missing_sidechain_heavy_atoms(lines)
    if not missing_sidechain_atoms:
        logging.info("No missing side chain heavy atoms detected. No action needed.")
        return    

    # Convert lines into residues indexed by residue_key (chain_id, seq_num, ins_code, res_name) and atom_name
    residues = {}
    for line in lines:
        if line.startswith(("ATOM  ")):
            residue_key, atom_name = line_indexed_by_atom(line)
            if residue_key not in residues:
                residues[residue_key] = {}
            residues[residue_key][atom_name] = line  # store line only

    # Load ideal structures for side chain completion
    ideal_structures_folder = default_ideal_structures_folder()
    ideal_structures_coords = {}
    for ideal_file in Path(ideal_structures_folder).glob("*.pdb"):
        res_name = ideal_file.stem[:3].upper()  # residue name is first 3 letters of the file name
        ideal_lines = open(ideal_file).readlines()
        for line in ideal_lines:
            if line.startswith(("ATOM  ", "HETATM")):
                atom_name = line[12:16]
                if is_H(atom_name):
                    continue  # skip hydrogens
                if res_name not in ideal_structures_coords:
                    ideal_structures_coords[res_name] = {}
                ideal_structures_coords[res_name][atom_name] = np.array(line[30:54].split(), dtype=float)

    # Replace the side chain if any heavy atoms are missing
    # Method:
    # Go through all lines (from pdb_file) and write to a new list of lines
    # When encountering a residue with missing side chain heavy atoms,
    #   1. Get the backbone atom coordinates from the original structure
    #   2. Get the ideal structure coordinates for that residue
    #   3. Align the ideal structure to the backbone N-CA-C atoms
    #   4. Replace the side chain atoms in the original structure with the aligned ideal structure
    new_lines = []

    # These variables track residues with missing heavy atoms that is being processed
    missing_residue = Missing_Residue()
 
    for line in lines:
        if line.startswith(("ATOM  ")):
            residue_key, atom_name = line_indexed_by_atom(line)
            if residue_key in missing_sidechain_atoms:
                # We are in a residue with missing side chain heavy atoms, check if we are still in the same missing residue
                if missing_residue.key != residue_key:
                    logging.debug(f"New missing residue encountered: {residue_key}, previous: {missing_residue.key}")
                    # New missing residue encountered, process the previous one if any
                    if missing_residue.key is not None:
                        # Complete the previous missing residue
                        new_lines.extend(missing_residue.complete_lines(ideal_structures_coords, residues))   # Complete the residue lines
                    # Reset for the new missing residue
                    missing_residue.key = residue_key
                    missing_residue.backbone_coords = {}
                    missing_residue.backbone_lines = []
                    missing_residue.sidechain_lines = []
                    if atom_name in backbone_atoms:
                        coord = np.array(line[30:54].split(), dtype=float)
                        missing_residue.backbone_coords[atom_name] = coord
                        missing_residue.backbone_lines.append(line)
                    else:
                        missing_residue.sidechain_lines.append(line)  # keep side chain lines in case we can't complete
                else: 
                    # Continuing in the same missing residue, collect backbone atom coordinates and ignore side chain atoms
                    if atom_name in backbone_atoms:
                        coord = np.array(line[30:54].split(), dtype=float)
                        missing_residue.backbone_coords[atom_name] = coord
                        missing_residue.backbone_lines.append(line)
                    else:
                        missing_residue.sidechain_lines.append(line)  # keep side chain lines in case we can't complete
            else:  # Not a missing side chain residue
                # If we were processing a missing residue, complete it first
                if missing_residue.key is not None:
                    # Complete the previous missing residue
                    new_lines.extend(missing_residue.complete_lines(ideal_structures_coords, residues))   # Complete the residue lines
                    # Reset missing residue tracking variables
                    missing_residue.key = None
                    missing_residue.backbone_coords = {}
                    missing_residue.backbone_lines = []
                    missing_residue.sidechain_lines = []
                # Now write the current line as is
                new_lines.append(line)
        else:
            new_lines.append(line)  # Non-atom lines are copied as is

    # Process the last missing residue if any
    if missing_residue.key is not None:
        # Complete the previous missing residue
        new_lines.extend(missing_residue.complete_lines(ideal_structures_coords, residues))   # Complete the residue lines

    # Write the new lines to a new PDB file
    p = Path(pdb_file)
    new_pdb_file = str(p.with_name(p.stem + "_completed" + p.suffix))
    with open(new_pdb_file, "w") as f:
        f.writelines(new_lines)
    logging.info(f"Completed side chain heavy atoms in {new_pdb_file}")


    if optimize:
        logging.info("Optimizing side chain completion...NOT IMPLEMENTED YET")
    return
