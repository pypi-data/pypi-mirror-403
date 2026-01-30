import logging
import typer
from . import core

app = typer.Typer(
    help="MCCE tools: A collection of utilities for manipulating MCCE files",
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
def pdb2ftpl(
    pdb_file: str = typer.Argument(..., help="PDB file of a single cofactor to be converted to ftpl file"),
    ignore_connect: bool = typer.Option(
        False,
        "--ignore-connect",
        help="Ignore CONNECT records in the PDB file (default: False)"
    ),
):
    """Convert a single cofactor PDB file to an ftpl template file."""
    logger = logging.getLogger("mccetools.pdb2ftpl")
    logger.debug(f"Converting PDB file {pdb_file} to ftpl template")
    core.pdb2ftpl(pdb_file, ignore_connect=ignore_connect)
