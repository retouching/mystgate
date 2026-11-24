import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from mystgate.core.logging.enums import LogColumn

LOG_DEPTH: ContextVar[int] = ContextVar("log_depth", default=0)
LOG_COLUMN: ContextVar[LogColumn | None] = ContextVar("log_column", default=None)


class LogContext:
    @classmethod
    @contextmanager
    def nested(cls) -> Iterator[None]:
        """Increase indentation depth for log records emitted inside the block."""
        token = LOG_DEPTH.set(LOG_DEPTH.get() + 1)
        try:
            yield
        finally:
            LOG_DEPTH.reset(token)

    @classmethod
    @contextmanager
    def column(cls, name: LogColumn) -> Iterator[None]:
        """Bind a log column name for log records emitted inside the block."""
        token = LOG_COLUMN.set(name)
        try:
            yield
        finally:
            LOG_COLUMN.reset(token)

    @staticmethod
    def keep_place(record: logging.LogRecord) -> bool:
        """Attach the current depth and column to a log record once."""
        if not hasattr(record, "log_depth"):
            record.log_depth = LOG_DEPTH.get()
        if not hasattr(record, "log_column"):
            current = LOG_COLUMN.get()
            record.log_column = current.value if current is not None else LogColumn.CLI.value
        return True
