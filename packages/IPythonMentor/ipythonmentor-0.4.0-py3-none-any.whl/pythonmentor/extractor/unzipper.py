import zipfile
import tempfile
import shutil
from pathlib import Path

LAST_ERROR = None

def resolve_input_path(path: str) -> tuple[str, bool]:
    global LAST_ERROR
    LAST_ERROR = None

    if not path:
        LAST_ERROR = "missing_path"
        return "", False

    try:
        p = Path(path)

        if p.is_file() and zipfile.is_zipfile(p):
            temp_dir = Path(tempfile.mkdtemp(prefix="extracted_"))
            try:
                with zipfile.ZipFile(p, "r") as z:
                    z.extractall(temp_dir)
            except (zipfile.BadZipFile, OSError):
                LAST_ERROR = "bad_zip"
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except OSError:
                    pass
                return "", False
            return str(temp_dir), True

        if p.exists():
            return str(p), False

        LAST_ERROR = "path_not_found"
        return "", False
    except OSError:
        LAST_ERROR = "os_error"
        return "", False


def get_last_error() -> str | None:
    return LAST_ERROR
