import re
from types import MappingProxyType
from typing import Final

DURATION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([smhd]?)\s*$", re.IGNORECASE)
DURATION_MULTIPLIERS: Final[MappingProxyType[str, float]] = MappingProxyType(
    {
        "": 1.0,
        "s": 1.0,
        "m": 60.0,
        "h": 3600.0,
        "d": 86400.0,
    }
)


def printable(value: str) -> str:
    """Escape control characters so untrusted text cannot corrupt logs or terminals."""
    return "".join(ch if ch.isprintable() else f"\\x{ord(ch):02x}" for ch in value)


def parse_duration(value: str) -> float:
    """Parse a human duration string such as 30s, 15m, or 1h into seconds."""
    match = DURATION_PATTERN.match(value)
    if match is None:
        raise ValueError(f"invalid duration: {value!r}")
    amount = float(match.group(1))
    unit = match.group(2).lower()
    seconds = amount * DURATION_MULTIPLIERS[unit]
    if seconds <= 0:
        raise ValueError(f"duration must be positive: {value!r}")
    return seconds
