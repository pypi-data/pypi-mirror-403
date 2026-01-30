import logging
import typer
from rich.traceback import install
from importlib.metadata import version, PackageNotFoundError, metadata
from . import core


try:
    __version__ = version("pymcce")
    meta = metadata("pymcce")
    __email__ = meta.get("Author-email", "unknown")
except PackageNotFoundError:
    __author__ = "unknown"
    __email__ = "unknown"
    __version__ = "unknown"


def print_version():
    typer.echo(f"PyMCCE version: {__version__}")
    typer.echo(f"PyMCCE developer: {__email__}")


app = typer.Typer(
    help="PyMCCE: Python MCCE simulation package with multiple subcommands",
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
        #format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        format="%(asctime)s [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# -----------------------------
# Global callback
# -----------------------------
@app.callback()
def main(
    log_level: str = typer.Option(
        "INFO", 
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
):
    """Configure logging before running any command."""
    setup_logging(log_level)


# -----------------------------
# Global version command
# -----------------------------
@app.command("version")
def version_cmd():
    """Show PyMCCE version."""
    print_version()


# -----------------------------
# Commands
# -----------------------------

def _preprocess(
    input_file: str = typer.Argument(..., help="Path to the input file"),
    noter: bool = typer.Option(
        False, "--noter", "-nt", help="Do not create terminal residues NTR and CTR"
    ),
    no_water: bool = typer.Option(
        False, "--no-water", "-nw", help="Remove all water molecules"
    ),
    ftpl: str = typer.Option(None, "--ftpl", "-f", help="Path to alternative ftpl (molecule topology) folder"),
    prm: str = typer.Option(None, "--prm", "-p", help="Path to alternative prm (mcce run behavior) file"),
    rename: str = typer.Option(None, "--rename", "-r", help="Path to alternative renaming rules file"),
    sas_cutoff: str = typer.Option("0.05", "--sas-cutoff", "-sc", help="SAS cutoff"),
):
    """Prepare input data and preprocess files. Alias: step1"""
    if input_file is None:
        typer.echo("Error: input_file is required for preprocessing.")
        raise typer.Exit(code=1)
    logger = logging.getLogger("pymcce.preprocess")
    logger.debug(
        f"Running preprocessing step on {input_file} with noter={noter}, no_water={no_water}, ftpl={ftpl}, prm={prm}, sas_cutoff={sas_cutoff}, rename={rename}"
    )
    core.preprocess(input_file, noter, no_water, ftpl, prm, sas_cutoff, rename)

app.command("preprocess")(_preprocess)
app.command("step1", hidden=True)(_preprocess)  # alias

def validate_level(value: int):
    if value is None:
        return None
    if not (1 <= value <= 3):
        raise typer.BadParameter("level must be between 1 and 3")
    return value

def _conformers(
    ftpl: str = typer.Option(None, "--ftpl", "-f", help="Path to alternative ftpl (molecule topology) folder"),
    prm: str = typer.Option(None, "--prm", "-p", help="Path to alternative prm (mcce run behavior) file"),
    level: int = typer.Option(
        None,
        "--level",
        "-lv",
        help="Level of conformer generation detail (1-3)",
        callback=validate_level,
    ),
    no_hdir: bool = typer.Option(
        False, "--no-hdir", "-nh",
        help="Disable H-bond directed rotamer generation, default is enabled"
    ),
    max_iter: int = typer.Option(None, "--max-iter", "-mi", help="Maximum iterations for sidechain optimization"),
    cluster_rmsd: float = typer.Option(None, "--cluster-rmsd", "-cr", help="RMSD threshold for clustering conformers"),
):
    """Generate conformers. Alias: step2"""
    logger = logging.getLogger("pymcce.conformers")
    logger.info(f"Generating conformers with level {level}, max_iter {max_iter}, cluster_rmsd {cluster_rmsd}...")
    install(show_locals=False)
    core.conformers(ftpl, prm, level, no_hdir, max_iter, cluster_rmsd)
    
app.command("conformers")(_conformers)
app.command("step2", hidden=True)(_conformers)  # alias


@app.command()
def energy():
    """Calculate energy."""
    logger = logging.getLogger("pymcce.energy")
    logger.info("Calculating energy...")
    # call core.energy()


@app.command()
def simulation():
    """Perform simulation."""
    logger = logging.getLogger("pymcce.simulation")
    logger.info("Running simulation procedure...")
    # call core.simulation()