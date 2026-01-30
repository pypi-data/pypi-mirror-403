import os
import logging
import pytest

from pdbtools import split_models


def test_file_not_found(caplog):
    with caplog.at_level(logging.ERROR):
        result = split_models("nonexistent.pdb")
    assert result is None
    assert "not found" in caplog.text


def test_valid_multi_model(tmp_path, caplog):
    pdb_file = tmp_path / "test.pdb"
    pdb_file.write_text(
        "HEADER Example PDB\n"
        "MODEL        1\n"
        "ATOM      1  N   MET A   1      11.104  13.207   2.000\n"
        "ENDMDL\n"
        "MODEL        2\n"
        "ATOM      2  CA  MET A   1      12.000  14.000   2.500\n"
        "ENDMDL\n"
    )

    with caplog.at_level(logging.INFO):
        split_models(str(pdb_file))

    # Verify output files exist
    model1 = tmp_path / "test_model_1.pdb"
    model2 = tmp_path / "test_model_2.pdb"

    assert model1.exists()
    assert model2.exists()

    assert "Wrote model 1" in caplog.text
    assert "Wrote model 2" in caplog.text

    # Verify content
    assert "ATOM      1" in model1.read_text()
    assert "ATOM      2" in model2.read_text()


def test_single_model_without_model_records(tmp_path, caplog):
    pdb_file = tmp_path / "single.pdb"
    pdb_file.write_text(
        "ATOM      1  N   MET A   1      11.104  13.207   2.000\n"
        "ATOM      2  CA  MET A   1      12.000  14.000   2.500\n"
    )

    with caplog.at_level(logging.WARNING):
        result = split_models(str(pdb_file))

    assert result is None
    assert "No MODEL/ENDMDL records" in caplog.text


def test_empty_file(tmp_path, caplog):
    pdb_file = tmp_path / "empty.pdb"
    pdb_file.write_text("")

    with caplog.at_level(logging.WARNING):
        result = split_models(str(pdb_file))

    assert result is None
    assert "No models found" in caplog.text