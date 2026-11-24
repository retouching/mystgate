import time


class Monotonic:
    def __call__(self) -> float:
        """Return the current monotonic clock reading in seconds."""
        return time.monotonic()
