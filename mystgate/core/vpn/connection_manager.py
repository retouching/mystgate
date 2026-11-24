import logging
from pathlib import Path
from typing import Final

from mystgate.core.exceptions import WireGuardError
from mystgate.core.logging import LogMarker
from mystgate.core.mysterium import MysteriumClient, TokenStore
from mystgate.core.utils import message
from mystgate.core.vpn.models import ConnectOptions, ConnectResult, LocalStatus
from mystgate.core.vpn.state_store import StateStore
from mystgate.core.wireguard import ConfigWriter, KeyGenerator, KeyPair

LOGGER: Final[logging.Logger] = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, client: MysteriumClient, state_store: StateStore) -> None:
        """Initialize WireGuard connection and session management."""
        self.client = client
        self.state_store = state_store

    def resolve_keypair(self, *, from_config: Path | None = None, new_key: bool = False) -> KeyPair:
        """Select the WireGuard keypair from an existing config, a fresh key, or local state."""
        if from_config is not None:
            return KeyGenerator.from_config_file(from_config)
        if new_key:
            return KeyGenerator.generate()
        return self.state_store.load_or_create_keypair()

    def connect(self, options: ConnectOptions) -> ConnectResult:
        """Request a WireGuard configuration from Mysterium and optionally write it in 0600 mode."""
        keypair = self.resolve_keypair(from_config=options.from_config, new_key=options.new_key)
        response = self.client.connect(
            keypair.public_key,
            options.country,
            options.ip_type,
            city=options.city,
            reset_connection=True,
        )
        rendered = ConfigWriter.render_template(response.wg_config, keypair)
        metadata = response.metadata()

        written_path: Path | None = None
        if not options.stdout_only:
            destination = options.output if options.output is not None else self.state_store.wg_config_path
            allow_overwrite = options.overwrite or options.output is None
            written_path = ConfigWriter.write_template(
                response.wg_config,
                keypair,
                destination,
                overwrite=allow_overwrite,
            )

        if options.from_config is None and not options.new_key:
            self.state_store.save_session(metadata)

        LOGGER.info(
            "%s Connected country=%s ip_type=%s exit_ip=%s",
            LogMarker.DONE.value,
            metadata.country,
            metadata.ip_type,
            metadata.exit_ip,
        )
        return ConnectResult(
            metadata=metadata,
            config_path=written_path,
            rendered_config=rendered,
            public_key=keypair.public_key,
        )

    def disconnect(self, *, config_path: Path | None = None, public_key: str | None = None) -> str:
        """Release the server-side session for a given public key, config file, or local keypair."""
        resolved_key = public_key
        if resolved_key is None and config_path is not None:
            resolved_key = KeyGenerator.from_config_file(config_path).public_key
        if resolved_key is None:
            existing = self.state_store.load_keypair()
            if existing is None:
                raise WireGuardError(
                    message("Disconnect", "no local WireGuard keypair found", "pass --config or --public-key")
                )
            resolved_key = existing.public_key

        self.client.disconnect(resolved_key)
        LOGGER.info("%s Disconnected session", LogMarker.DONE.value)
        return resolved_key

    def status(self, token_store: TokenStore) -> LocalStatus:
        """Return local authentication, keypair, and last session status."""
        keypair = self.state_store.load_keypair()
        return LocalStatus(
            signed_in=token_store.exists(),
            public_key=keypair.public_key if keypair is not None else None,
            session=self.state_store.load_session(),
            state_directory=self.state_store.directory,
        )
