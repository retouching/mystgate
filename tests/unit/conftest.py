import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
import pytest_socket

from mystgate.core.logging import LogContext
from tests.support import Isolation
from tests.unit.support import ColumnRecorder


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Disable network sockets during unit tests unless explicitly marked."""
    if item.get_closest_marker("enable_socket") is not None:
        pytest_socket.enable_socket()
        return
    pytest_socket.disable_socket(allow_unix_socket=True)


@pytest.fixture(autouse=True)
def isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Isolate environment variables, HOME, and CWD for every unit test."""
    Isolation.apply(tmp_path, monkeypatch)
    yield tmp_path
    pytest_socket.enable_socket()


@pytest.fixture
def columns() -> Iterator[ColumnRecorder]:
    """Capture log records emitted to mystgate logger with column and depth."""
    logger = logging.getLogger("mystgate")
    recorder = ColumnRecorder()
    recorder.addFilter(LogContext.keep_place)
    logger.addHandler(recorder)
    try:
        yield recorder
    finally:
        logger.removeHandler(recorder)
