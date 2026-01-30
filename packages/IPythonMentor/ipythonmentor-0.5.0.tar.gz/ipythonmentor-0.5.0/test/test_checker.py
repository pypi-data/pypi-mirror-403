from pythonmentor.dir.checker import get_file_by_type


def test_get_file_by_type_returns_first_match(tmp_path):
    (tmp_path / "a.py").write_text("print('a')")
    (tmp_path / "b.py").write_text("print('b')")

    found = get_file_by_type(str(tmp_path), ".py")

    assert found in {"a.py", "b.py"}


def test_get_file_by_type_returns_none_when_missing(tmp_path):
    (tmp_path / "a.txt").write_text("nope")

    found = get_file_by_type(str(tmp_path), ".py")

    assert found is None
