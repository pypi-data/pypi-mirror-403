import builtins
import logging
import os
from unittest.mock import patch, MagicMock
import pytest

from pdbtools import getpdb  # <-- replace "yourmodule" with the actual module name


def test_getpdb_success(tmp_path, caplog):
    pdb_name = "1abc"
    pdb_content = b"MOCK PDB DATA"

    # Patch requests.get to return a mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = pdb_content

    with patch("requests.get", return_value=mock_response):
        # Run inside tmp_path so files are written there
        cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with caplog.at_level(logging.INFO):
                getpdb(pdb_name)

            # Check that file was written
            outfile = tmp_path / f"{pdb_name}.pdb"
            assert outfile.exists()
            assert outfile.read_bytes() == pdb_content

            # Check logging message
            assert f"Downloaded {pdb_name}.pdb" in caplog.text
        finally:
            os.chdir(cwd)


def test_getpdb_failure(tmp_path, caplog):
    pdb_name = "2xyz"

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.content = b""

    with patch("requests.get", return_value=mock_response):
        cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with caplog.at_level(logging.ERROR):
                getpdb(pdb_name)

            # File should not exist
            outfile = tmp_path / f"{pdb_name}.pdb"
            assert not outfile.exists()

            # Check logging error message
            assert f"Failed to download {pdb_name}.pdb" in caplog.text
        finally:
            os.chdir(cwd)