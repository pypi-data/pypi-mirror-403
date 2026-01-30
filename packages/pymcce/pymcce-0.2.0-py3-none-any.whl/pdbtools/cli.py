import logging
import typer
from . import core

app = typer.Typer(
    help="PDB tools: A collection of Utilities for facilitating MCCE runs and analyzing their output",
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True
)

# -----------------------------
# Logging setup
# -----------------------------
def setup_logging(level: str = "INFO"):
    """Configure root logger with simple text format."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        # Alternative format with logger name:
        # "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        format="%(asctime)s [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# -----------------------------
# Global callback
# -----------------------------
@app.callback()
def main(
    log_level: str = typer.Option(
        "INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
):
    """Configure logging before running any command."""
    setup_logging(log_level)


# -----------------------------
# Commands
# -----------------------------

@app.command()
def getpdb(
    pdb: list[str] = typer.Argument(..., help="PDB name(s) to download"),
):
    """Download one or more PDB files from Protein Data Bank using the given PDB name(s) (e.g., 1akk)."""
    logger = logging.getLogger("pdbtools.getpdb")
    for pdb_name in pdb:
        logger.debug(f"Downloading PDB file for {pdb_name}")
        core.getpdb(pdb_name)

@app.command()
def complete_sidechain(
    pdb_file: str = typer.Argument(..., help="Input PDB file"),
    optimize: bool = typer.Option(False, "--optimize", help="Optimize the added side chain atoms")
):
    """Complete side chain atoms in a PDB file."""
    logger = logging.getLogger("pdbtools.complete_sidechain")
    logger.debug(f"Completing side chain atoms in {pdb_file}")
    core.complete_sidechain(pdb_file, optimize)

@app.command()
def split_models(
    pdb_file: str = typer.Argument(..., help="Input PDB file"),
):
    """Split a PDB file into separate models."""
    logger = logging.getLogger("pdbtools.split_models")
    logger.debug(f"Splitting models in {pdb_file}")
    core.split_models(pdb_file)

@app.command()
def split_altlocs(
    pdb_file: str = typer.Argument(..., help="Input PDB file"),
):
    """Split a PDB file into separate alternate locations."""
    logger = logging.getLogger("pdbtools.split_altlocs")
    logger.debug(f"Splitting alternate locations in {pdb_file} if that happens on the backbone atoms")
    core.split_altlocs(pdb_file)

@app.command()
def mcce_readiness(
    pdb_file: str = typer.Argument(..., help="Input PDB file"),
):
    """Check if a PDB file is ready for MCCE processing."""
    logger = logging.getLogger("pdbtools.mcce_readiness")
    logger.debug(f"Checking MCCE readiness for {pdb_file}")
    messages = core.mcce_readiness(pdb_file)
    core.print_summary(messages)

