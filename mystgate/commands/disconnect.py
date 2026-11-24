from pathlib import Path

import click

from mystgate.core.config import Settings
from mystgate.core.logging import LogColumn, LogContext, LoggingSession, Terminal
from mystgate.core.mysterium import MysteriumClient, TokenStore
from mystgate.core.vpn import ConnectionManager, StateStore


class DisconnectCommand(click.Command):
    def __init__(self) -> None:
        """Define the disconnect CLI command."""
        super().__init__(
            name="disconnect",
            help="Release a server-side Mysterium VPN WireGuard session.",
            params=[
                click.Option(
                    ["--config", "config_path"],
                    type=click.Path(path_type=Path, exists=True, dir_okay=False),
                    default=None,
                    help="Derive the public key locally from a WireGuard .conf file and disconnect it.",
                ),
                click.Option(
                    ["--public-key"],
                    default=None,
                    help="Disconnect a specific WireGuard public key.",
                ),
            ],
            callback=self.execute,
        )

    @staticmethod
    def execute(config_path: Path | None, public_key: str | None) -> None:
        """Disconnect the selected WireGuard session."""
        settings = Settings.load()
        terminal = Terminal()
        token_store = TokenStore(settings.state_directory)
        state_store = StateStore(settings.state_directory)

        with (
            LoggingSession(
                settings.log_directory,
                debug=settings.debug,
                secrets=settings.secrets(),
                console_enabled=settings.debug,
            ),
            LogContext.column(LogColumn.WIREGUARD),
            MysteriumClient(settings, token_store=token_store) as client,
        ):
            manager = ConnectionManager(client, state_store)
            with terminal.status("Disconnecting session..."):
                disconnected_key = manager.disconnect(config_path=config_path, public_key=public_key)

        terminal.print_info(f"Disconnected. Public key: {disconnected_key}")
