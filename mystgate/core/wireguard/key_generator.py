import base64
import re
from pathlib import Path
from typing import Final

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from pydantic import SecretStr

from mystgate.core.exceptions import WireGuardError
from mystgate.core.utils import message
from mystgate.core.wireguard.models import KeyPair

KEY_LENGTH_BYTES: Final[int] = 32
PRIVATE_KEY_LINE: Final[re.Pattern[str]] = re.compile(r"^\s*PrivateKey\s*=\s*(\S+)\s*$", re.MULTILINE)


class KeyGenerator:
    @staticmethod
    def generate() -> KeyPair:
        """Generate a new WireGuard X25519 keypair encoded in base64."""
        private = X25519PrivateKey.generate()
        private_bytes = private.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return KeyPair(
            private_key=SecretStr(base64.b64encode(private_bytes).decode("ascii")),
            public_key=base64.b64encode(public_bytes).decode("ascii"),
        )

    @staticmethod
    def derive_public_key(private_key: str) -> str:
        """Derive the base64-encoded WireGuard public key from a private key."""
        try:
            raw = base64.b64decode(private_key.strip(), validate=True)
        except ValueError as error:
            raise WireGuardError(message("WireGuard key", "invalid encoding")) from error

        if len(raw) != KEY_LENGTH_BYTES:
            raise WireGuardError(message("WireGuard key", "invalid length", f"expected {KEY_LENGTH_BYTES} bytes"))

        private = X25519PrivateKey.from_private_bytes(raw)
        public_bytes = private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(public_bytes).decode("ascii")

    @classmethod
    def from_private_key(cls, private_key: str) -> KeyPair:
        """Build a KeyPair by validating and deriving the public key from a private key."""
        cleaned = private_key.strip()
        return KeyPair(private_key=SecretStr(cleaned), public_key=cls.derive_public_key(cleaned))

    @classmethod
    def from_config_file(cls, path: Path) -> KeyPair:
        """Read a WireGuard .conf file and extract its KeyPair from PrivateKey."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            raise WireGuardError(message("WireGuard config", "cannot read file", str(path), str(error))) from error

        match = PRIVATE_KEY_LINE.search(text)
        if match is None:
            raise WireGuardError(message("WireGuard config", "missing PrivateKey field", str(path)))
        return cls.from_private_key(match.group(1))
