import json
from pythonmentor.processors.processor import combine


def test_combine_reads_python_and_ipynb(tmp_path):
    py_file = tmp_path / "core.py"
    py_file.write_text("print('hi')")

    nb_file = tmp_path / "demo.ipynb"
    nb = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Title"]},
            {"cell_type": "code", "source": ["x = 1\n", "print(x)\n"]},
        ]
    }
    nb_file.write_text(json.dumps(nb))

    result = combine(str(tmp_path))

    assert "# --- core.py ---" in result
    assert "print('hi')" in result
    assert "# --- demo.ipynb ---" in result
    assert "x = 1" in result
    assert "# Title" not in result


def test_combine_skips_macosx_and_dot_underscore(tmp_path):
    mac_dir = tmp_path / "__MACOSX"
    mac_dir.mkdir()
    (mac_dir / "ignored.py").write_text("print('ignored')")
    (tmp_path / "._noise.py").write_text("print('ignored')")

    result = combine(str(tmp_path))

    assert "ignored" not in result
