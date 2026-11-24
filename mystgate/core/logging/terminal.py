import json
import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import TextIO

from mystgate.core.exceptions import MystgateError


class Terminal:
    def __init__(self, stdout: TextIO | None = None, stderr: TextIO | None = None) -> None:
        """Initialize plain stdout and stderr streams."""
        self.stdout = stdout if stdout is not None else sys.stdout
        self.stderr = stderr if stderr is not None else sys.stderr

    def print_text(self, text: str) -> None:
        """Write plain text to stdout."""
        self.stdout.write(f"{text}\n")
        self.stdout.flush()

    def print_info(self, text: str) -> None:
        """Write an informational message to stderr."""
        self.stderr.write(f"{text}\n")
        self.stderr.flush()

    def print_json(self, payload: object) -> None:
        """Write formatted JSON to stdout."""
        self.stdout.write(f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n")
        self.stdout.flush()

    def print_table(
        self,
        title: str,
        columns: Sequence[str],
        rows: Sequence[Sequence[str]],
    ) -> None:
        """Render a plain aligned table to stdout."""
        del title
        widths = [len(name) for name in columns]
        for row in rows:
            for index, cell in enumerate(row):
                if index < len(widths):
                    widths[index] = max(widths[index], len(cell))

        header = "  ".join(name.ljust(widths[index]) for index, name in enumerate(columns))
        separator = "  ".join("-" * width for width in widths)
        lines = [header, separator]
        for row in rows:
            lines.append("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))
        self.print_text("\n".join(lines))

    def print_key_values(
        self,
        title: str,
        rows: Sequence[tuple[str, str]],
        *,
        note: str | None = None,
    ) -> None:
        """Render aligned key-value pairs to stdout with an optional stderr note."""
        del title
        width = max((len(label) for label, _ in rows), default=0)
        lines = [f"{label.ljust(width)} : {value}" for label, value in rows]
        self.print_text("\n".join(lines))
        if note is not None:
            self.print_info(note)

    def print_panel(self, body: str, *, title: str) -> None:
        """Write a titled message block to stderr."""
        self.print_info(f"{title}\n{body}")

    def print_error(self, error: MystgateError) -> None:
        """Write a formatted domain error to stderr."""
        self.print_info(f"Error: {error}")

    @contextmanager
    def status(self, text: str) -> Iterator[None]:
        """Execute a block without terminal spinner decoration."""
        del text
        yield
