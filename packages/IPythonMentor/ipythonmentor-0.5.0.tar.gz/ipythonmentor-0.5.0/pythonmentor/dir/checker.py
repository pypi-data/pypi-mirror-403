from pathlib import Path

def get_file_by_type(directory: str, extension: str):
    if not directory:
        return None
    if not extension:
        return None

    try:
        path = Path(directory)
        if not path.exists():
            return None
        if path.is_file():
            return path.name if path.suffix == extension else None
        if not path.is_dir():
            return None

        for file in path.glob(f"*{extension}"):
            return file.name
        return None
    except OSError:
        return None
