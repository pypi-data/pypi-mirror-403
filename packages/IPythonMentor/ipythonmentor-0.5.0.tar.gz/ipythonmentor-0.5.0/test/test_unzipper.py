import zipfile
from pathlib import Path
from pythonmentor.extractor.unzipper import resolve_input_path


def test_resolve_input_path_returns_existing_directory(tmp_path):
    path, is_temp = resolve_input_path(str(tmp_path))

    assert path == str(tmp_path)
    assert is_temp is False


def test_resolve_input_path_extracts_zip(tmp_path):
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "a.py").write_text("print('ok')")

    zip_path = tmp_path / "archive.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(payload / "a.py", arcname="a.py")

    extracted_path, is_temp = resolve_input_path(str(zip_path))

    extracted = Path(extracted_path)
    assert is_temp is True
    assert extracted.exists()
    assert (extracted / "a.py").exists()


def test_resolve_input_path_returns_empty_for_missing_path(tmp_path):
    missing = tmp_path / "missing"

    path, is_temp = resolve_input_path(str(missing))

    assert path == ""
    assert is_temp is False
