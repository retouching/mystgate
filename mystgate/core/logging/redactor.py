import re
from collections.abc import Iterable
from typing import Final

URL_PASSWORD_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<=://)(?P<lead>[^\s/?#:@]*:)[^\s/]+(?=@[^\s/?#@]*(?:[\s/?#]|$))"
)
KEY_VALUE_SECRET_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)(?P<lead>\b(?:password|secret|token|private_key|preshared_key|access_token|refresh_token)\s*[:=]\s*)"
    r"(?P<val>\"[^\"]*\"|'[^']*'|[^\s,;]+)"
)
REDACTED_MARKER: Final[str] = "<redacted>"


class Redactor:
    def __init__(self, secrets: Iterable[str] = ()) -> None:
        """Build a secret redactor for URLs, sensitive key-value pairs, and explicit values."""
        unique = sorted({item for item in secrets if item}, key=len, reverse=True)
        self.patterns: tuple[re.Pattern[str], ...] = tuple(
            re.compile(rf"(?<![\w-]){re.escape(secret)}(?![\w-])") for secret in unique
        )

    def scrub(self, text: str) -> str:
        """Replace all matching secrets in text with a redaction placeholder."""
        cleaned = URL_PASSWORD_PATTERN.sub(rf"\g<lead>{REDACTED_MARKER}", text)
        cleaned = KEY_VALUE_SECRET_PATTERN.sub(rf"\g<lead>{REDACTED_MARKER}", cleaned)
        for pattern in self.patterns:
            cleaned = pattern.sub(REDACTED_MARKER, cleaned)
        return cleaned
