from pathlib import Path

import pytest

from tests.support import Isolation


@pytest.fixture(autouse=True)
def isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate environment variables, HOME, and CWD for integration tests."""
    return Isolation.apply(tmp_path, monkeypatch)
