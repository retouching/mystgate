import json
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from mystgate.core.exceptions import WireGuardError
from mystgate.core.mysterium import SessionMetadata
from mystgate.core.utils import message, write_private
from mystgate.core.wireguard import KeyGenerator, KeyPair

KEYPAIR_FILENAME: Final[str] = "keypair.json"
SESSION_FILENAME: Final[str] = "session.json"
WG_CONF_FILENAME: Final[str] = "wg.conf"


class StateStore:
    def __init__(self, directory: Path) -> None:
        """Bind local WireGuard and session state files to a directory."""
        self.directory = directory
        self.keypair_path = directory / KEYPAIR_FILENAME
        self.session_path = directory / SESSION_FILENAME
        self.wg_config_path = directory / WG_CONF_FILENAME

    def load_keypair(self) -> KeyPair | None:
        """Load the saved local WireGuard keypair if present."""
        if not self.keypair_path.is_file():
            return None
        try:
            raw = json.loads(self.keypair_path.read_text(encoding="utf-8"))
            return KeyPair.model_validate(raw)
        except (OSError, ValueError, ValidationError) as error:
            raise WireGuardError(message("State", "invalid saved keypair", str(self.keypair_path))) from error

    def save_keypair(self, keypair: KeyPair) -> Path:
        """Persist a WireGuard keypair atomically with 0600 permissions."""
        payload = {
            "private_key": keypair.private_key.get_secret_value(),
            "public_key": keypair.public_key,
        }
        return write_private(self.keypair_path, json.dumps(payload, indent=2) + "\n")

    def load_or_create_keypair(self) -> KeyPair:
        """Return the saved local keypair or generate and persist a new one."""
        existing = self.load_keypair()
        if existing is not None:
            return existing
        pair = KeyGenerator.generate()
        self.save_keypair(pair)
        return pair

    def load_session(self) -> SessionMetadata | None:
        """Load the last saved session metadata if present."""
        if not self.session_path.is_file():
            return None
        try:
            raw = json.loads(self.session_path.read_text(encoding="utf-8"))
            return SessionMetadata.model_validate(raw)
        except OSError, ValueError, ValidationError:
            return None

    def save_session(self, metadata: SessionMetadata) -> Path:
        """Persist session metadata atomically with 0600 permissions."""
        return write_private(self.session_path, metadata.model_dump_json(indent=2) + "\n")
