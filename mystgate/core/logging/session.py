import logging
import sys
from collections.abc import Iterable
from pathlib import Path
from types import TracebackType
from typing import Final, TextIO

from mystgate.core.logging.context import LogContext
from mystgate.core.logging.files import LogFiles
from mystgate.core.logging.formatter import ConsoleFormatter
from mystgate.core.logging.redactor import Redactor

LOGGER_NAME: Final[str] = "mystgate"


class LoggingSession:
    def __init__(
        self,
        directory: Path,
        *,
        debug: bool = False,
        secrets: Iterable[str] = (),
        stream: TextIO | None = None,
        console_enabled: bool = True,
    ) -> None:
        """Configure a scoped logging session with stderr output and rotating JSON files."""
        self.directory = directory
        self.debug = debug
        self.redactor = Redactor(secrets)
        self.stream = stream if stream is not None else sys.stderr
        self.console_enabled = console_enabled
        self.logger = logging.getLogger(LOGGER_NAME)
        self.handlers: list[logging.Handler] = []
        self.previous_level = self.logger.level
        self.previous_propagate = self.logger.propagate

    def __enter__(self) -> LoggingSession:
        """Attach console and rotating file handlers to the package logger."""
        self.previous_level = self.logger.level
        self.previous_propagate = self.logger.propagate
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        file_handler = LogFiles.open(self.directory, self.redactor)
        file_handler.addFilter(LogContext.keep_place)
        self.logger.addHandler(file_handler)
        self.handlers.append(file_handler)

        if self.console_enabled:
            console_handler = logging.StreamHandler(self.stream)
            console_handler.setLevel(logging.DEBUG if self.debug else logging.INFO)
            console_handler.setFormatter(
                ConsoleFormatter(self.redactor, color=ConsoleFormatter.supports_color(self.stream))
            )
            console_handler.addFilter(LogContext.keep_place)
            self.logger.addHandler(console_handler)
            self.handlers.append(console_handler)

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Detach and close all handlers created by this logging session."""
        del exc_type, exc_val, exc_tb
        self.close()

    def close(self) -> None:
        """Remove session handlers, close file descriptors, and restore logger state."""
        for handler in self.handlers:
            self.logger.removeHandler(handler)
            handler.close()
        self.handlers.clear()
        self.logger.setLevel(self.previous_level)
        self.logger.propagate = self.previous_propagate
