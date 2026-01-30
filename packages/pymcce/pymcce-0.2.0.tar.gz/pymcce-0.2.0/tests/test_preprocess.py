import shutil
import subprocess
import pytest
from pathlib import Path

test_cases = [
    ("4lzt/4lzt.pdb", [
        "## Conformer ID=HOH01A1073_001 History=01O000_000", # comment line for a water
        "SSBOND   3 CYS A   64_   CYS A   80_ SS  1555   1555  2.02",  # disulfide bond line
        "ATOM    346  CB  THR A0043_002   7.294   3.693  24.804   1.700       0.000      01B000_000", # altloc in a conformer
    ]),
    ("1akk/1akk.pdb", [
        "LINK         NE2 HIL A  18_               FE   HEM A 105_    1555   1555  1.95", # ligand detection line
        "HETATM  860  O1A PAA A0105_001   1.432  -5.492  -4.890   1.520       0.000      01O000_000",  # split PAA from HEM
        "HETATM  824 FE   HEM A0105_001   4.144   0.732  -0.600   1.800       0.000      01O000_000", # HEC renamed to HEM
    ]),
    ("4lzt_newtpl/4lzt_newtpl.pdb", [
        "ATOM   1019  OH  TXR A0020_001 -12.413  18.259  28.152   1.520       0.000      ??O000_000", # Unknown cofactor TXR
    ]),
    # Add more cases here
]


@pytest.mark.parametrize("pdb_file, expected_lines", test_cases)
def test_preprocess_multiple_files(tmp_path, pdb_file, expected_lines):
    """
    Test pymcce preprocess:
    1. Create a temporary folder.
    2. Copy input pdb file into it.
    3. Run `pymcce preprocess <pdb>`.
    4. Verify step1_out.pdb exists.
    5. Verify expected lines are present.
    """

    # Paths
    pdb_source = Path(pdb_file).resolve()
    assert pdb_source.exists(), f"Input file {pdb_source} not found."

    pdb_copy = tmp_path / pdb_source.name
    shutil.copy(pdb_source, pdb_copy)

    # Run preprocess command inside tmp_path
    result = subprocess.run(
        ["pymcce", "preprocess", pdb_copy.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    # Check command executed successfully
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Check output file created
    out_file = tmp_path / "step1_out.pdb"
    assert out_file.exists(), "Output file step1_out.pdb was not created."

    # Read output
    contents = out_file.read_text().splitlines()

    # Verify expected patterns
    for expected in expected_lines:
        assert any(expected in line for line in contents), \
            f"Expected pattern '{expected}' not found in step1_out.pdb"