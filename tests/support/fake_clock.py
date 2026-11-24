from datetime import UTC, datetime, timedelta

from mystgate.core.utils import Clock


class FakeClock(Clock):
    def __init__(self, current: datetime | None = None) -> None:
        """Initialize a controllable UTC clock for deterministic tests."""
        self.current = current if current is not None else datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    def now(self) -> datetime:  # type: ignore[override]
        """Return the current fixed UTC datetime."""
        return self.current

    def advance(self, seconds: float) -> None:
        """Advance the fake clock by the given number of seconds."""
        self.current = self.current + timedelta(seconds=seconds)
