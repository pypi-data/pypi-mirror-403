import pytest
from importlib import resources

def test_ftpl_resources():
    # Point to the ftpl directory inside the package
    folder_res = resources.files("pymcce.data").joinpath("ftpl")

    # Resolve to a usable path (works for both editable and wheel installs)
    with resources.as_file(folder_res) as folder_path:
        # Check the directory exists
        assert folder_path.exists(), f"ftpl folder not found at {folder_path}"
        assert folder_path.is_dir(), f"{folder_path} is not a directory"

        # Check that expected files are there
        ftpl_files = list(folder_path.glob("*.ftpl"))
        assert ftpl_files, "No .ftpl files found in ftpl folder"

        # Example: ensure specific required files are included
        expected = {"ala.ftpl", "arg.ftpl", "_zn.ftpl"}
        found = {f.name for f in ftpl_files}
        missing = expected - found
        assert not missing, f"Missing expected ftpl files: {missing}"
