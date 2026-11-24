import json
from pathlib import Path
from typing import Final

LOG_FILENAME: Final[str] = "mystgate.log"


class JSONLog:
    @staticmethod
    def read(directory: Path) -> list[dict[str, object]]:
        """Parse every JSON log line from mystgate.log in the given directory."""
        path = directory / LOG_FILENAME
        if not path.is_file():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
