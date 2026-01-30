from pathlib import Path
import json

def combine(path: str) -> str:
    if not path:
        return ""

    p = Path(path)
    if not p.exists():
        return ""

    texts = []

    files = [p] if p.is_file() else p.rglob("*")

    for file in files:
        if not file.is_file():
            continue
        if "__MACOSX" in file.parts or file.name.startswith("._"):
            continue
        if file.suffix == ".py":
            texts.append(f"\n# --- {file.name} ---\n")
            try:
                texts.append(file.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue

        elif file.suffix == ".ipynb":
            texts.append(f"\n# --- {file.name} ---\n")
            try:
                nb = json.loads(file.read_text(encoding="utf-8", errors="ignore"))
            except (OSError, json.JSONDecodeError):
                continue
            for cell in nb.get("cells", []):
                if cell.get("cell_type") == "code":
                    texts.append("".join(cell.get("source", [])))

    return "\n".join(texts)
