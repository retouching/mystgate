import os
from pathlib import Path

import pytest


class Isolation:
    @staticmethod
    def apply(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Clear MYSTGATE_* variables and isolate HOME and CWD to a temporary directory."""
        for key in list(os.environ):
            if key.startswith("MYSTGATE_"):
                monkeypatch.delenv(key, raising=False)
        home_dir = tmp_path / "home"
        home_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("HOME", str(home_dir))
        monkeypatch.chdir(tmp_path)
        return tmp_path
