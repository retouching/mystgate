import json
import logging
from datetime import UTC, datetime

from mystgate.core.logging.redactor import Redactor


class JSONFormatter(logging.Formatter):
    def __init__(self, redactor: Redactor) -> None:
        """Initialize the structured JSON lines formatter with secret redaction."""
        super().__init__()
        self.redactor = redactor

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record to a single redacted JSON line."""
        moment = datetime.fromtimestamp(record.created, tz=UTC).isoformat()
        payload: dict[str, object] = {
            "time": moment,
            "level": record.levelname,
            "logger": record.name,
            "column": str(getattr(record, "log_column", "cli")),
            "message": self.redactor.scrub(record.getMessage()),
        }
        if record.exc_info is not None:
            payload["exception"] = self.redactor.scrub(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False)
