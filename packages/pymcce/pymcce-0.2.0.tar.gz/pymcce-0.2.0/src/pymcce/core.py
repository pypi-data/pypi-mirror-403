"""
Core functionality for PyMCCE.

This module will contain the main computational functions and classes
for molecular dynamics calculations and continuum electrostatics.

Functions are MCCE data structures oriented by the nature.

Author: Junjun Mao
Organization: City College of New York
"""

import logging
from importlib import resources
from .mcce import *
from .constants import *

def preprocess(
    input_file: str,
    noter: bool,
    no_water: bool,
    ftpl: str,
    prm: str,
    sas_cutoff: float,
    rename: str
) -> None:
    """
    Preprocess the input molecular structure file for MCCE calculations.

    This function performs a series of steps to prepare the input structure for
    multi-conformation continuum electrostatics calculations using MCCE. It
    handles terminal residue creation, water removal, SAS-based filtering, ligand
    identification, hierarchy construction, conformer assignment, and outputs
    all necessary files for subsequent MCCE steps.

    Parameters
    ----------
    input_file : str
        Path to the input molecular structure file (typically PDB format).
    noter : bool
        If True, do not create terminal residues NTR and CTR.
    no_water : bool
        If True, remove all water molecules from the structure.
    ftpl : str
        Path to custom molecule topology (ftpl) folder.
    prm : str
        Path to custom MCCE run behavior (prm) file.
    sas_cutoff : float
        Solvent Accessible Surface Area cutoff for filtering exposed cofactors.
    rename : str
        Path to renaming rules file for residue/atom names.

    Outputs
    -------
    step1_out.pdb : Preprocessed molecular structure file ready for MCCE calculations.
    head1.lst : List of residue properties.
    preprocess.prm : Parameters used in preprocessing.
    new.tpl : Topology file templates for unknown cofactors (if present).

    Raises
    ------
    SystemExit
        If preprocessing fails at any step.
    """

    logging.info(f"Starting preprocessing for {input_file}")

    # Initialize MCCE object with provided parameter and topology files
    mcce = MCCE(prm=prm, ftpl=ftpl)

    # Update MCCE parameters based on input arguments
    mcce.prm['SAS_CUTOFF'] = str(float(sas_cutoff))
    mcce.prm['TERMINALS'] = 'f' if noter else 't'
    mcce.prm['NO_HOH'] = 't' if no_water else 'f'

    # Load user-defined topology files if available
    if os.path.isdir(USER_FTPL):
        logging.info(f"Detected user-defined ftpl folder: ./{USER_FTPL}")
        mcce.load_ftpl_files(USER_FTPL)

    # Load renaming rules if provided
    mcce.load_rename_rules(rename)

    # Read and process the input PDB file
    mcce.read_plainpdb(input_file)
    mcce.rename_pdb()
    mcce.pdblines2atoms()

    # Remove water molecules if requested
    if mcce.prm['NO_HOH'] == 't':
        logging.info("Removing water molecules from the structure.")
        mcce.remove_waters()

    # Filter exposed cofactors by SAS cutoff
    mcce.strip_exposed_cofactors(sas_cutoff)

    # Identify ligands and build protein hierarchy
    mcce.identify_ligands()
    mcce.build_hierarchy()

    # Add terminal residues if requested
    if mcce.prm["TERMINALS"] == 't':
        mcce.split_terminal_residues()

    # Assign conformer types
    mcce.assign_conftypes()

    # Write output files
    mcce.write_mccepdb(STEP1_OUT)
    mcce.write_head1_lst(HEAD1_LST)
    mcce.dump_prm(PREPROCESS_PRM_DUMP)
    mcce.tpl.dump(FTPL_DUMP)

    logging.info("Preprocessing completed successfully.")

    # Output summary
    line_width = 80
    align_width = 20
    print("\n" + "=" * line_width)
    print("Preprocessing completed. Output summary:")
    print("-" * line_width)
    print(f"  - {STEP1_OUT:<{align_width}}: Preprocessed structure file.")
    print(f"  - {HEAD1_LST:<{align_width}}: Residue properties list.")
    print(f"  - {PREPROCESS_PRM_DUMP:<{align_width}}: Used parameters.")
    print(f"  - {FTPL_DUMP:<{align_width}}: Topology records.")
    print("=" * line_width)


def conformers(
    ftpl: str | None = None,
    prm: str | None = None,
    level: int | None = None,
    no_hdir: bool = False,
    max_iter: int | None = None,
    cluster_rmsd: float | None = None
) -> None:
    """
    Generate conformers for residues in the preprocessed structure.

    This function reads the preprocessed structure and generates multiple
    conformations for each residue based on the specified level of detail.
    It optimizes sidechain orientations and ensures that the number of
    conformers does not exceed the specified maximum.

    Parameters
    ----------
    ftpl : str | None, optional
        Path to custom molecule topology (ftpl) folder. None keeps existing.
    prm : str | None, optional
        Path to custom MCCE run behavior (prm) file. None keeps existing.
    level : int | None, optional
        Level of conformer generation detail (1-3, 1 is lowest). None keeps existing.
    no_hdir : bool, optional
        If True, disable H-bond directed rotamer generation. Default is False (enabled).
    max_iter : int | None, optional
        Maximum iterations for sidechain optimization. None keeps existing.
    cluster_rmsd : float | None, optional
        RMSD threshold for clustering conformers. None keeps existing.

    Outputs
    -------
    step2_out.pdb : Structure file with generated conformers.
    head2.lst : List of generated conformers and their properties.

    Raises
    ------
    SystemExit
        If conformer generation fails at any step.
    """

    logging.info("Starting conformer generation.")

    # Initialize MCCE object with provided parameter and topology files
    mcce = MCCE(prm=prm, ftpl=ftpl)

    # Load user-defined topology files if available
    if os.path.isdir(USER_FTPL):
        logging.info(f"Detected user-defined ftpl folder: ./{USER_FTPL}")
        mcce.load_ftpl_files(USER_FTPL)

    # Modify prm by command line specified run levels (only if provided)
    if level is not None:
        if level == 1:
            prm_file = str(resources.files("pymcce.data.prm").joinpath(ROTAMER_LEVEL1_PRM))
        elif level == 2:
            prm_file = str(resources.files("pymcce.data.prm").joinpath(ROTAMER_LEVEL2_PRM))
        elif level == 3:
            prm_file = str(resources.files("pymcce.data.prm").joinpath(ROTAMER_LEVEL3_PRM))
        else:
            logging.error("Invalid level specified. Must be 1, 2, or 3.")
            exit(1)

        logging.info(f"Updating run parameters from {prm_file} for conformer generation at level {level}.")
        mcce.load_prm_file(prm_file)
    else:
        logging.info("No conformer level specified; keeping existing prm settings.")

    # Modify prm by command line specified hdir (only if provided)
    if no_hdir:
        logging.info("Disabling H-bond directed rotamer generation.")
        mcce.prm["HDIRECTED"] = 'f'

    # Modify prm by command line specified max_iter and cluster_rmsd (only if provided)
    if max_iter is not None:
        logging.info(f"Setting MAX_ITER to {max_iter}.")
        mcce.prm['MAX_ITER'] = str(max_iter)
    if cluster_rmsd is not None:
        logging.info(f"Setting CLUSTER_RMSD to {cluster_rmsd}.")
        mcce.prm['CLUSTER_RMSD'] = str(cluster_rmsd)

    # Read preprocessed PDB file and head1.lst
    mcce.read_mccepdb(STEP1_OUT)
    logging.info(f"Loaded preprocessed structure from {STEP1_OUT}.")

    # Place OXT
    mcce.make_connect12()
    mcce.check_connect_symmetry()
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug("Dumping connectivity for debugging purposes.")
        mcce.dump_connectivity()
    n_placed = mcce.place_oxt()
    logging.info(f"Placed {n_placed} OXT atom(s) on CTR.")

    # Generate conformers
    mcce.write_rot_stat()  # Initialize rotamer statistics
    mcce.write_rot_stat(step="start", rot_stat_file=ROT_STAT)
    logging.info(f"Counted initial rotamers, wrote to {ROT_STAT}.")

    # 1. Swap conformers
    mcce.rot_swap()
    mcce.write_rot_stat(step="swap", rot_stat_file=ROT_STAT)
    logging.info(f"Made swap rotamers, wrote to {ROT_STAT}.")

    # 2. Rotate/Swing
    mcce.rotate_rules = make_rotate_rules(mcce.tpl)
    logging.info(f"Created rotate rules for {len(mcce.rotate_rules)} conftypes based on ROTATE and CONNECT in ftpl files.")
    if mcce.rotate_rules:
        logging.debug("rotate_rules:")
        for key, value in mcce.rotate_rules.items():
            logging.debug("  %s: %s", key, value)
    else:
        logging.debug("rotate_rules: <none>")
    
    if mcce.prm["SWING"] == 't':
        n_new = mcce.rot_swing()
        logging.info(f"Swing sidechains, generated {n_new} conformer(s).")
    else:
        logging.info("SWING is set to false; skipping sidechain swinging.")

    if mcce.prm["PACK"] == 't':
        n_new = mcce.rot_rotate()
        logging.info(f"Rotate sidechains, generated {n_new} conformer(s).")
    else:
        logging.info("PACK is set to false; skipping sidechain rotating.")

    mcce.write_rot_stat(step="rotate", rot_stat_file=ROT_STAT)
    logging.info(f"Rotamer making stats written to {ROT_STAT}.")

    # 3. Self-energy conformer clean by VDW, only necessary when either mcce.prm["PACK"] or mcce.prm["SWING"] is true
    if mcce.prm["PACK"] == 't' or mcce.prm["SWING"] == 't':
        logging.info("Starting self-energy conformer clean by VDW to limit number of conformers per residue.")
        n_removed = mcce.self_clean()
        logging.info(f"Self-energy conformer clean done, removed {n_removed} conformer(s), wrote to {ROT_STAT}.")
    mcce.write_rot_stat(step="clean", rot_stat_file=ROT_STAT)
    
    # 4. Hbond directed
    if mcce.prm["HDIRECTED"] == 't':
        logging.info("Starting hydrogen bond directed rotamer generation.")
        n_new = mcce.hbond_directed_rotamers()
        logging.info(f"Generated {n_new} Hbond directed rotamer(s).")
        logging.info(f"Hbond directed rotamer stats written to {ROT_STAT}.")
    mcce.write_rot_stat(step="hbond", rot_stat_file=ROT_STAT)
    
    # 5. Energy minimization - Repack sidechains if any extensive rotamer making (PACK, SWING, HDIRECTED) is true
    if mcce.prm["PACK"] == 't' or mcce.prm["SWING"] == 't' or mcce.prm["HDIRECTED"] == 't':
        logging.info("Starting sidechain repacking via energy minimization.")
        n_deleted = mcce.repack_sidechains()
        logging.info(f"Sidechain repacking done, reduced {n_deleted} conformers.")
    mcce.write_rot_stat(step="repack", rot_stat_file=ROT_STAT)

    # 6. Most exposed rotamer making
    if mcce.prm["EXPOSED"] == 't':
        logging.info("Starting most exposed rotamer making.")
        n_new = mcce.most_exposed_rotamers()
        logging.info(f"Generated {n_new} most exposed rotamer(s).")
    mcce.write_rot_stat(step="xposed", rot_stat_file=ROT_STAT)

    # 7. Ionization/Protonation
    logging.info("Starting ionization/protonation conformer generation.")
    n_new = mcce.ionization_conformers()
    logging.info(f"Generated {n_new} ionization/protonation conformer(s).")
    mcce.write_rot_stat(step="ioni", rot_stat_file=ROT_STAT)

    # 8. H optimization
    logging.info("Starting hydrogen placement and optimization.")
    mcce.place_hydrogens()
    logging.info("Hydrogen placement and optimization completed.")
    mcce.write_rot_stat(step="torh", rot_stat_file=ROT_STAT)

    # 9. Optimize H atoms for hydrogen bonds
    logging.info("Starting hydrogen bond optimization.")
    mcce.optimize_hydrogen()
    logging.info("Hydrogen bond optimization completed.")
    mcce.write_rot_stat(step="oh", rot_stat_file=ROT_STAT)

    # 10. Cluster conformers
    logging.info("Starting conformer clustering.")
    n_removed = mcce.cluster_conformers()
    logging.info(f"Conformer clustering done, removed {n_removed} conformer(s), wrote to {ROT_STAT}.")
    mcce.write_rot_stat(step="cluster", rot_stat_file=ROT_STAT)

    # Write output files
    logging.info(f"Writing prm used by conformer generation to {CONFORMERS_PRM_DUMP}.")
    mcce.dump_prm(CONFORMERS_PRM_DUMP)

    mcce.sort_conformers()
    mcce.write_mccepdb(STEP2_OUT)