import os
from pathlib import Path
from typing import Final

PRIVATE_DIR_MODE: Final[int] = 0o700
PRIVATE_FILE_MODE: Final[int] = 0o600


def write_private(path: Path, content: str) -> Path:
    """Write text atomically to path with 0600 file permissions and 0700 parent directory."""
    path.parent.mkdir(mode=PRIVATE_DIR_MODE, parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    descriptor = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, PRIVATE_FILE_MODE)
    try:
        os.fchmod(descriptor, PRIVATE_FILE_MODE)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
    except Exception:
        os.close(descriptor)
        if temp_path.exists():
            temp_path.unlink()
        raise
    os.replace(temp_path, path)
    return path
