from pathlib import Path

import click

from mystgate.core.config import Settings
from mystgate.core.logging import LogColumn, LogContext, LoggingSession, Terminal
from mystgate.core.mysterium import IPType, MysteriumClient, TokenStore
from mystgate.core.vpn import ConnectionManager, ConnectOptions, StateStore


class ConnectCommand(click.Command):
    def __init__(self) -> None:
        """Define the connect CLI command for creating or rotating WireGuard configs."""
        super().__init__(
            name="connect",
            help="Create or rotate a WireGuard configuration from Mysterium VPN.",
            params=[
                click.Option(["--country", "-c"], required=True, help="Two-letter ISO country code (e.g. FR, US)."),
                click.Option(["--city"], default=None, help="Optional city identifier."),
                click.Option(
                    ["--type", "-t", "ip_type_name"],
                    type=click.Choice([IPType.RESIDENTIAL.value, IPType.HOSTING.value], case_sensitive=False),
                    default=IPType.RESIDENTIAL.value,
                    show_default=True,
                    help="IP type to request.",
                ),
                click.Option(
                    ["--output", "-o"],
                    type=click.Path(path_type=Path, dir_okay=False),
                    default=None,
                    help="Output path for the WireGuard .conf file.",
                ),
                click.Option(
                    ["--force", "-f"],
                    is_flag=True,
                    default=False,
                    help="Overwrite the output file if it already exists.",
                ),
                click.Option(
                    ["--stdout", "stdout_only"],
                    is_flag=True,
                    default=False,
                    help="Print the rendered WireGuard config to stdout instead of writing a file.",
                ),
                click.Option(
                    ["--from-config"],
                    type=click.Path(path_type=Path, exists=True, dir_okay=False),
                    default=None,
                    help="Reuse the private key from an existing .conf file to change location or rotate IP.",
                ),
                click.Option(
                    ["--new-key"],
                    is_flag=True,
                    default=False,
                    help="Generate a brand-new WireGuard keypair (uses a separate device slot).",
                ),
                click.Option(
                    ["--json", "as_json"],
                    is_flag=True,
                    default=False,
                    help="Output session metadata as JSON on stdout.",
                ),
            ],
            callback=self.execute,
        )

    @staticmethod
    def execute(
        country: str,
        city: str | None,
        ip_type_name: str,
        output: Path | None,
        force: bool,
        stdout_only: bool,
        from_config: Path | None,
        new_key: bool,
        as_json: bool,
    ) -> None:
        """Request a WireGuard configuration and write or print it."""
        settings = Settings.load()
        terminal = Terminal()
        token_store = TokenStore(settings.state_directory)
        state_store = StateStore(settings.state_directory)
        options = ConnectOptions(
            country=country,
            ip_type=IPType(ip_type_name),
            city=city,
            output=output,
            overwrite=force,
            stdout_only=stdout_only,
            from_config=from_config,
            new_key=new_key,
        )

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
            status_text = f"Requesting WireGuard config ({options.country.upper()} / {options.ip_type.value})..."
            with terminal.status(status_text):
                result = manager.connect(options)

        if options.stdout_only:
            terminal.print_text(result.rendered_config.rstrip("\n"))
            return

        if as_json:
            terminal.print_json(
                {
                    "session": result.metadata.model_dump(mode="json"),
                    "config_path": str(result.config_path) if result.config_path is not None else None,
                    "public_key": result.public_key,
                }
            )
            return

        terminal.print_key_values(
            "WireGuard Session",
            [
                ("Country", result.metadata.country or "-"),
                ("City", result.metadata.city or "-"),
                ("Type", result.metadata.ip_type or "-"),
                ("Exit IP", result.metadata.exit_ip or "-"),
                ("Public key", result.public_key),
                ("Config file", str(result.config_path) if result.config_path is not None else "-"),
            ],
        )
