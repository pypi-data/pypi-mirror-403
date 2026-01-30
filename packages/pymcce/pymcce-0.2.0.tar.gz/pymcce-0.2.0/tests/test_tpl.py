# test_tpl.py
import pytest
import tempfile
import os
import datetime
import logging

from pymcce import Tpl   # assuming your class is in tpl.py


@pytest.fixture
def tpl():
    return Tpl()


def test_dict_like_behavior(tpl):
    key = ("TEST", "A", "")
    tpl[key] = "value"
    assert tpl[key] == "value"
    assert key in tpl
    assert tpl.get(key) == "value"

    del tpl[key]
    assert key not in tpl
    assert tpl.get(key, "default") == "default"


def test_connect_param():
    param = Tpl.CONNECT_param('sp2, " ?  ", " CA ", " H  "')
    assert param.orbital == "sp2"
    assert " CA " in param.connected
    assert str(param) == 'sp2, " ?  ", " CA ", " H  "'


def test_radius_param():
    param = Tpl.RADIUS_param("1.500, 1.824, 0.170")
    assert pytest.approx(param.r_bound) == 1.5
    assert pytest.approx(param.r_vdw) == 1.824
    assert pytest.approx(param.e_vdw) == 0.170
    assert "1.5" in str(param)


def test_conformer_param():
    param = Tpl.CONFORMER_param("Em0=0.0, pKa0=2.0, ne=1, nH=2")
    assert param.em0 == 0.0
    assert param.pka0 == 2.0
    assert param.ne == 1
    assert "em0" in str(param)  # internally the keys were converted to lowercase
    assert "pka0" in str(param)
    assert "ne" in str(param)
    assert "nh" in str(param)

def test_rotate_param():
    param = Tpl.ROTATE_param('" CA " - " CB ", " CB " - " CG "')
    assert (" CA ", " CB ") in param.rotatables
    assert '" CA " - " CB "' in str(param)


def test_rot_swap_param():
    param = Tpl.ROT_SWAP_param('" ND1" - " CD2", " CE1" - " NE2"')
    assert (" ND1", " CD2") in param.swapables
    assert '" ND1" - " CD2"' in str(param)


def test_ligand_id_param():
    s = '" SG " - " SG "; 2.00 +- 0.20; CYL, CYL'
    param = Tpl.LIGAND_ID_param(s)
    assert param.atom1 == " SG "
    assert param.atom2 == " SG "
    assert pytest.approx(param.distance) == 2.0
    assert pytest.approx(param.tolerance) == 0.2
    assert param.res1_name == "CYL"
    assert str(param).startswith('" SG " - " SG "; 2.0')


def test_load_ftpl_file(tmp_path):
    content = """# Comment
CONFLIST, ASP: ASPBK, ASP01, ASP02
CONNECT, " N  ", ASPBK: sp2, " ?  ", " CA "
RADIUS, ASPBK, " N  ": 1.500, 1.824, 0.170
CHARGE, ASPBK, " N  ": -0.5
"""
    fpath = tmp_path / "test.ftpl"
    fpath.write_text(content)

    tpl = Tpl()
    tpl.load_ftpl_file(fpath)

    assert ("CONFLIST", "ASP") in tpl
    assert isinstance(tpl[("CONNECT", " N  ", "ASPBK")], Tpl.CONNECT_param)
    assert isinstance(tpl[("RADIUS", "ASPBK", " N  ")], Tpl.RADIUS_param)
    assert tpl[("CHARGE", "ASPBK", " N  ")] == -0.5


def test_dump_creates_file(tmp_path):
    tpl = Tpl()
    tpl[("CHARGE", "ASPBK", " N  ")] = -1.23

    FTPL_DUMP = tmp_path / "out.tpl"

    tpl.dump(file_path=FTPL_DUMP, comment="# test dump")
    text = FTPL_DUMP.read_text()

    assert "CHARGE, ASPBK, \" N  \"" in text or "CHARGE" in text
    assert "-1.23" in text
    assert "# test dump" in text
