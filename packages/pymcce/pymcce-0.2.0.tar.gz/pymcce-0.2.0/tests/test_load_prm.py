import tempfile
import logging
import os
import pytest

class DummyClass:
    def __init__(self):
        self.default_prm = "fallback"
        self.prm = {}
        self.prm_file = None

    def load_prm_file(self, prm: str):
        prm_file = prm if prm else f"{self.default_prm}.prm"
        logging.info(f"Loading prm file from {prm_file}")
        self.prm_file = prm_file

        with open(prm_file, 'r') as f:
            for line in f:
                line = line.split('#', 1)[0].strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[-1].startswith('(') and parts[-1].endswith(')'):
                    key = parts[-1][1:-1].strip()
                    value = parts[0].strip()
                    self.prm[key] = value


def test_load_prm_file(tmp_path, caplog):
    # Arrange: create a fake prm file
    prm_content = """
    10 param1   (KEY1)   # comment
    20 param2   (KEY2)
    # This is a full-line comment
    30 param3   (KEY3)
    """

    prm_file = tmp_path / "test.prm"
    prm_file.write_text(prm_content)

    obj = DummyClass()

    # Act: call the method
    with caplog.at_level(logging.INFO):
        obj.load_prm_file(str(prm_file))

    # Assert: check values were parsed
    assert obj.prm_file == str(prm_file)
    assert obj.prm == {
        "KEY1": "10",
        "KEY2": "20",
        "KEY3": "30",
    }

    # Assert: check logging message
    assert f"Loading prm file from {prm_file}" in caplog.text