import numpy as np
import pytest
import logging
from pymcce.mcce import MCCE

# Minimal data/constants/functions used by make_connect12
ATOM_RADII = {"C": 0.76, "H": 0.31, "O": 0.66, "S": 1.05}
ATOM_RADIUS_UNKNOWN = 0.7


def is_H(atomname: str) -> bool:
    return "H" in atomname.strip()


class ConnectParams:
    def __init__(self, connected):
        self.connected = connected


class MockAtom:
    def __init__(self, atomname, element, xyz, resid=None):
        self.atomname = atomname
        self.element = element
        self.xyz = xyz
        self.connect12 = []
        self.resid = resid


class MockConformer:
    def __init__(self, atoms, conftype="BK", confid="conf1"):
        self.atoms = atoms
        self.conftype = conftype
        self.confid = confid


class MockResidue:
    def __init__(self, conformers, resname="RES", resid=1, chain="A"):
        self.conformers = conformers
        self.resname = resname
        self.resid = resid
        self.chain = chain


class MockProtein:
    def __init__(self, residues):
        self.residues = residues


class DummyMCCE:
    def __init__(self, protein, tpl):
        self.protein = protein
        self.tpl = tpl

    def reset_connect(self):
        for res in self.protein.residues:
            for conf in res.conformers:
                for atom in conf.atoms:
                    atom.connect12 = []

    # Copy of the target method, adapted to work in this test module's scope
    make_connect12 = MCCE.make_connect12
# Tests

def test_named_connection_within_same_conformer():
    # Two atoms in the same conformer, A connects to B by name
    a = MockAtom("A", "C", (0.0, 0.0, 0.0))
    b = MockAtom("B", "C", (1.0, 0.0, 0.0))
    conf = MockConformer([a, b], conftype="BK")
    res = MockResidue([conf], resname="RES", resid=1)
    protein = MockProtein([res])

    tpl = {("CONNECT", "A", "RESBK"): ConnectParams(["B"],),
           ("CONNECT", "B", "RESBK"): ConnectParams(["A"],),
        }
    mcce = DummyMCCE(protein, tpl)
    mcce.make_connect12()

    assert b in a.connect12
    assert a in b.connect12


def test_question_connection_between_residues_based_on_distance():
    # Two residues, atom in first has "?" connect, atom in second also has "?" connect,
    # atoms are close enough to satisfy covalent + tolerance
    a = MockAtom("X", "C", (0.0, 0.0, 0.0), resid=1)
    conf1 = MockConformer([a], conftype="-1")
    res1 = MockResidue([conf1], resname="RES", resid=1)

    b = MockAtom("Y", "C", (0.7, 0.0, 0.0), resid=2)  # distance 0.7 < C+C (0.76*2)+0.45
    conf2 = MockConformer([b], conftype="01")
    res2 = MockResidue([conf2], resname="RES", resid=2)

    protein = MockProtein([res1, res2])
    tpl = {
        ("CONNECT", "X", "RES-1"): ConnectParams(["?"]),
        ("CONNECT", "Y", "RES01"): ConnectParams(["?"]),
    }
    mcce = DummyMCCE(protein, tpl)
    mcce.make_connect12()

    assert b in a.connect12
    assert a in b.connect12


def test_cyl_sg_connects_to_named_other_even_if_other_has_no_question():
    # CYL SG has "?" in its connect list, other atom has no connect params;
    # special-case branch should still connect them if within distance
    sg = MockAtom(" SG ", "S", (0.0, 0.0, 0.0), resid=1)
    conf1 = MockConformer([sg], conftype="01")
    res1 = MockResidue([conf1], resname="CYL", resid=1)

    other = MockAtom("ZN", "C", (1.0, 0.0, 0.0), resid=2)
    conf2 = MockConformer([other], conftype="01")
    res2 = MockResidue([conf2], resname="MISC", resid=2)

    protein = MockProtein([res1, res2])
    tpl = {
        ("CONNECT", " SG ", "CYL01"): ConnectParams(["?"]),
        # note: no ("CONNECT", "ZN", ... ) entry, to trigger the special-case elif
    }
    mcce = DummyMCCE(protein, tpl)
    mcce.make_connect12()

    assert other in sg.connect12
    assert sg in other.connect12


def test_ntr_and_ctr_connections_are_found_across_residues():
    # test CA connecting to previous NTR residue
    prev_ca = MockAtom(" CA ", "C", (0.0, 0.0, 0.0), resid=1)
    prev_conf = MockConformer([prev_ca], conftype="BK")
    prev_res = MockResidue([prev_conf], resname="NTR", resid=1, chain="A")

    # current residue has an atom that wants to connect to " CA "
    cur_atom = MockAtom("X", "C", (1.0, 0.0, 0.0), resid=2)
    cur_conf = MockConformer([cur_atom], conftype="BK")
    cur_res = MockResidue([cur_conf], resname="RES", resid=2, chain="A")

    # next residue CTR for C connection
    next_c = MockAtom(" C  ", "C", (2.0, 0.0, 0.0), resid=3)
    next_conf = MockConformer([next_c], conftype="BK")
    next_res = MockResidue([next_conf], resname="CTR", resid=3, chain="A")

    protein = MockProtein([prev_res, cur_res, next_res])
    tpl = {
        ("CONNECT", "X", "RESBK"): ConnectParams([" CA ", " C  "]),
    }
    mcce = DummyMCCE(protein, tpl)
    mcce.make_connect12()

    # cur_atom should have connected to prev_ca via NTR rule and to next_c via CTR rule
    assert prev_ca in cur_atom.connect12
    assert cur_atom in prev_ca.connect12
    assert next_c in cur_atom.connect12
    assert cur_atom in next_c.connect12