import pytest
import logging

from pymcce.mcce import MCCE  # adjust import path if different

def test_rename_pdb_basic():
    # Sample PDB lines
    pdblines = [
        "ATOM   1666  HA  GLU A 104     -14.693   6.334  -6.576  1.00  0.00           H\n",
        "HETATM 1672 FE   HEC A 105       4.144   0.732  -0.600  1.00  0.00          FE\n",
        "HETATM 1673  CAA HEC A 105       3.000   1.000   0.000  1.00  0.00           C\n",

    ]

    # Simple rename rules: GLU → GLX, HEC → HEM
    rename_rules = [
        ("*****GLU******", "*****GLX******"),
        ("*****HEC******", "*****HEM******"),
        ("*CAA*HEM******", "*****PAA******"),  # test sequential renaming
    ]

    mcce = MCCE()
    mcce.pdblines = pdblines
    mcce.rename_rules = rename_rules
    mcce.rename_pdb()

    # After renaming
    new_lines = mcce.pdblines

    # GLU → GLX
    assert "GLX" in new_lines[0][12:26]
    # HEC → HEM
    assert "HEM" in new_lines[1][12:26]
    # CAA HEC → PAA
    assert "PAA" in new_lines[2][12:26]
    assert "HEM" not in new_lines[2][12:26]

