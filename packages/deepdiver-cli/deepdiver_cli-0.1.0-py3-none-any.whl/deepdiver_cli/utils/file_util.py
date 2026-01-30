from pathlib import Path
from typing import Set


def read_text(path: Path) -> str:
    """
    read text content from the path
    """
    if path.exists():
        return path.read_text(encoding="utf-8")
    raise ValueError(f"File not exists: {str(path)}")


def is_within_dirs(p: str, dirs: Set[str]) -> bool:
    try:
        rp = Path(p).expanduser().resolve()
        for dir in dirs:
            if rp.is_relative_to(Path(dir).expanduser().resolve()):
                return True
        return False
    except Exception:
        return False
