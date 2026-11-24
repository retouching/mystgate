from types import MappingProxyType
from typing import Final

CONSOLE_ONLY: Final[MappingProxyType[str, bool]] = MappingProxyType({"console_only": True})
UNREDACTED: Final[MappingProxyType[str, bool]] = MappingProxyType({"unredacted": True, "console_only": True})
