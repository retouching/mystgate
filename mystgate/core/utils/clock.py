from datetime import UTC, datetime


class Clock:
    @staticmethod
    def now() -> datetime:
        """Return the current UTC datetime."""
        return datetime.now(UTC)
