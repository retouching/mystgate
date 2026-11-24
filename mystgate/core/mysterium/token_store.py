import json
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from mystgate.core.exceptions import AuthenticationError
from mystgate.core.mysterium.schemas import OAuthTokens
from mystgate.core.utils import message, write_private

TOKENS_FILENAME: Final[str] = "tokens.json"


class TokenStore:
    def __init__(self, directory: Path) -> None:
        """Bind the token store to a state directory."""
        self.path = directory / TOKENS_FILENAME

    def exists(self) -> bool:
        """Check whether saved OAuth tokens exist on disk."""
        return self.path.is_file()

    def fingerprint(self) -> tuple[int, int] | None:
        """Return (mtime_ns, size) of tokens.json to detect external auth refreshes."""
        try:
            info = self.path.stat()
        except OSError:
            return None
        return (info.st_mtime_ns, info.st_size)

    def load(self) -> OAuthTokens:
        """Read and validate OAuth tokens from disk."""
        if not self.path.is_file():
            raise AuthenticationError(
                message("Authentication", "not signed in", f"run `mystgate auth` (missing {self.path})")
            )
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return OAuthTokens.model_validate(raw)
        except (OSError, ValueError, ValidationError) as error:
            raise AuthenticationError(message("Authentication", "invalid saved tokens", str(self.path))) from error

    def save(self, tokens: OAuthTokens) -> Path:
        """Persist OAuth tokens atomically with 0600 permissions."""
        payload = {
            "access_token": tokens.access_token.get_secret_value(),
            "refresh_token": tokens.refresh_token.get_secret_value(),
        }
        return write_private(self.path, json.dumps(payload, indent=2) + "\n")
