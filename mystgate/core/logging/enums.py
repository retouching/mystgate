from enum import StrEnum


class LogColumn(StrEnum):
    CLI = "cli"
    API = "api"
    WIREGUARD = "wireguard"
    CONFIG = "config"

    @classmethod
    def width(cls) -> int:
        """Return the maximum display width across all log columns."""
        return max(len(column.value) for column in cls)


class LogMarker(StrEnum):
    DONE = "[+]"
    SKIPPED = "[-]"
    PROBLEM = "[!]"
