from mystgate.core.utils import Monotonic


class FakeMonotonic(Monotonic):
    def __init__(self, current: float = 0.0) -> None:
        """Initialize a controllable monotonic timer."""
        self.current = current

    def __call__(self) -> float:
        """Return the current fake monotonic reading in seconds."""
        return self.current

    def advance(self, seconds: float) -> None:
        """Advance the fake monotonic reading by seconds."""
        self.current += seconds
