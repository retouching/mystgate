import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

from mystgate.core.exceptions import LoggingError
from mystgate.core.logging.files.json_formatter import JSONFormatter
from mystgate.core.logging.redactor import Redactor
from mystgate.core.utils import message

MAX_LOG_BYTES: Final[int] = 10 * 1024 * 1024
BACKUP_COUNT: Final[int] = 5
LOG_FILENAME: Final[str] = "mystgate.log"


class LogFiles:
    @staticmethod
    def skip_console_only(record: logging.LogRecord) -> bool:
        """Filter out log records marked as console-only."""
        return not bool(getattr(record, "console_only", False))

    @classmethod
    def open(cls, directory: Path, redactor: Redactor) -> RotatingFileHandler:
        """Create and configure the rotating JSON log file handler."""
        if directory.exists() and not directory.is_dir():
            raise LoggingError(message("Logging", "log directory is not a directory", str(directory)))
        try:
            directory.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                directory / LOG_FILENAME,
                maxBytes=MAX_LOG_BYTES,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
            )
        except OSError as error:
            raise LoggingError(message("Logging", "cannot open log file", str(directory), str(error))) from error

        handler.setLevel(logging.DEBUG)
        handler.setFormatter(JSONFormatter(redactor))
        handler.addFilter(cls.skip_console_only)
        return handler
