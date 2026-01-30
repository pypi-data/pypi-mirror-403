"""
PDB Tools: A collection of utilities for manipulating PDB files.

Some example tools include:
- Downloading PDB files from the Protein Data Bank
- Report summary statistics of a PDB file
- Split a PDB file into separate chains
- Split a PDB file into separate models
- Split a PDB file by altLocs on backbone atoms
"""

# Expose modules to outside callers
from .core import getpdb, split_models, split_altlocs, mcce_readiness

__all__ = ["getpdb", "split_models", "split_altlocs", "mcce_readiness"]