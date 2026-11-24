import logging


class ColumnRecorder(logging.Handler):
    def __init__(self) -> None:
        """Record emitted log records with their attached column and depth."""
        super().__init__()
        self.records: list[tuple[str, int, str]] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Store the column, depth, and formatted message of an emitted record."""
        column = str(getattr(record, "log_column", ""))
        depth = int(getattr(record, "log_depth", 0))
        self.records.append((column, depth, record.getMessage()))
