from pathlib import Path
from typing import Final

from mystgate.core.exceptions import WireGuardError
from mystgate.core.utils import message, write_private
from mystgate.core.wireguard.models import KeyPair

PRIVATE_KEY_PLACEHOLDER: Final[str] = "%private_key%"


class ConfigWriter:
    @staticmethod
    def render_template(template: str, keypair: KeyPair) -> str:
        """Substitute the private key placeholder inside a Mysterium WireGuard template."""
        if PRIVATE_KEY_PLACEHOLDER not in template:
            raise WireGuardError(message("WireGuard config", "template missing private key placeholder"))
        rendered = template.replace(PRIVATE_KEY_PLACEHOLDER, keypair.private_key.get_secret_value())
        return rendered if rendered.endswith("\n") else f"{rendered}\n"

    @classmethod
    def write_template(
        cls,
        template: str,
        keypair: KeyPair,
        destination: Path,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Render a Mysterium WireGuard template and write it atomically with 0600 permissions."""
        if destination.exists() and not overwrite:
            raise WireGuardError(message("WireGuard config", "output file already exists", str(destination)))
        rendered = cls.render_template(template, keypair)
        try:
            return write_private(destination, rendered)
        except OSError as error:
            raise WireGuardError(message("WireGuard config", "write failed", str(destination), str(error))) from error
