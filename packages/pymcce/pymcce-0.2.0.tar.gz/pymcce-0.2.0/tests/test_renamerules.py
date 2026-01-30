import pytest
import logging

@pytest.fixture
def loader():
    from pymcce.mcce import MCCE
    return MCCE()

def test_load_valid_rules(tmp_path, loader):
    # Create a temp file with valid and invalid lines
    rules_file = tmp_path / "rules.txt"
    rules_file.write_text(
        "ABCDEFGHIJKLMN  OPQRSTUVWXYZ  # valid line\n"
        "short line\n"
        "# comment only\n"
        "*CAA*HEM******  *****PAA******      extract propionate PAA from heme\n"
    )
    
    loader.load_rename_rules(str(rules_file))
    
    # Only the long line should be parsed
    assert len(loader.rename_rules) == 2   # two valid lines
    str_from, str_to = loader.rename_rules[0]
    assert str_from == "ABCDEFGHIJKLMN"[:14]
    assert str_to == "OPQRSTUVWXYZ  "[:14]
    str_from, str_to = loader.rename_rules[1]
    assert str_from == "*CAA*HEM******"[:14]
    assert str_to == "*****PAA******"[:14]

def test_load_no_file_uses_default(monkeypatch, tmp_path, loader):
    fake_file = tmp_path / "default_rules.txt"
    fake_file.write_text("ABCDEFGHIJKLMN  OPQRSTUVWXYZ  ")

    monkeypatch.setattr("pymcce.mcce.default_rename_file", lambda: str(fake_file))
    
    loader.load_rename_rules("")  # no file provided
    assert len(loader.rename_rules) == 1

def test_file_not_found_exits(monkeypatch, loader):
    # Make default return a nonexistent path
    monkeypatch.setattr("pymcce.mcce.default_rename_file", lambda: "no_such_file.txt")

    with pytest.raises(SystemExit):  # because exit(1) is called
        loader.load_rename_rules("")

def test_permission_error(monkeypatch, tmp_path, loader):
    bad_file = tmp_path / "rules.txt"
    bad_file.write_text("ABCDEFGHIJKLMN  OPQRSTUVWXYZ  ")

    # Monkeypatch open() to raise PermissionError
    def bad_open(*args, **kwargs):
        raise PermissionError("no permission")
    monkeypatch.setattr("builtins.open", bad_open)

    with pytest.raises(SystemExit):
        loader.load_rename_rules(str(bad_file))