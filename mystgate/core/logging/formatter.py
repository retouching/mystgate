import logging
import os
import sys
import time
from types import MappingProxyType
from typing import Final, TextIO

from mystgate.core.logging.enums import LogColumn, LogMarker
from mystgate.core.logging.indented_formatter import IndentedFormatter
from mystgate.core.logging.redactor import Redactor

LEVEL_TAGS: Final[MappingProxyType[int, tuple[str, str]]] = MappingProxyType(
    {
        logging.DEBUG: ("[D]", "90"),
        logging.INFO: ("[I]", "36"),
        logging.WARNING: ("[W]", "33"),
        logging.ERROR: ("[E]", "31"),
        logging.CRITICAL: ("[E]", "31"),
    }
)
ANSI_RESET: Final[str] = "\033[0m"


class ConsoleFormatter(IndentedFormatter):
    converter = staticmethod(time.gmtime)

    def __init__(self, redactor: Redactor, *, color: bool = False) -> None:
        """Initialize the UTC console log formatter with optional ANSI colors."""
        super().__init__(datefmt="%H:%M:%S")
        self.redactor = redactor
        self.color = color
        self.column_width = LogColumn.width()

    @staticmethod
    def supports_color(stream: TextIO | None = None) -> bool:
        """Determine whether ANSI color output should be enabled for the given stream."""
        target = stream if stream is not None else sys.stderr
        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("TERM") == "dumb":
            return False
        return hasattr(target, "isatty") and target.isatty()

    def paint(self, text: str, code: str) -> str:
        """Wrap text in ANSI escape codes when color output is enabled."""
        if not self.color:
            return text
        return f"\033[{code}m{text}{ANSI_RESET}"

    def style_markers(self, text: str, levelno: int) -> str:
        """Colorize known status markers in a formatted log message."""
        if not self.color:
            return text
        text = text.replace(LogMarker.DONE.value, self.paint(LogMarker.DONE.value, "32"))
        text = text.replace(LogMarker.SKIPPED.value, self.paint(LogMarker.SKIPPED.value, "90"))
        problem_color = "33" if levelno == logging.WARNING else "31"
        return text.replace(LogMarker.PROBLEM.value, self.paint(LogMarker.PROBLEM.value, problem_color))

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record into an aligned, optionally colored UTC console line."""
        timestamp = self.formatTime(record, self.datefmt)
        tag, color_code = LEVEL_TAGS.get(record.levelno, ("[I]", "36"))
        column = str(getattr(record, "log_column", LogColumn.CLI.value)).ljust(self.column_width)
        rendered = self.indent(record, record.getMessage())
        if not getattr(record, "unredacted", False):
            rendered = self.redactor.scrub(rendered)
        rendered = self.style_markers(rendered, record.levelno)
        return f"{timestamp} {self.paint(tag, color_code)} {column} : {rendered}"
