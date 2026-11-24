import click

from mystgate.core.config import Settings
from mystgate.core.logging import Terminal
from mystgate.core.mysterium import MysteriumClient, TokenStore
from mystgate.core.vpn import ConnectionManager, StateStore


class StatusCommand(click.Command):
    def __init__(self) -> None:
        """Define the status CLI command."""
        super().__init__(
            name="status",
            help="Show local authentication, WireGuard keypair, and last session status.",
            params=[
                click.Option(
                    ["--json", "as_json"],
                    is_flag=True,
                    default=False,
                    help="Output local status as JSON on stdout.",
                )
            ],
            callback=self.execute,
        )

    @staticmethod
    def execute(as_json: bool) -> None:
        """Read local state and display authentication and session status."""
        settings = Settings.load()
        terminal = Terminal()
        token_store = TokenStore(settings.state_directory)
        state_store = StateStore(settings.state_directory)

        with MysteriumClient(settings, token_store=token_store) as client:
            info = ConnectionManager(client, state_store).status(token_store)

        if as_json:
            terminal.print_json(info.model_dump(mode="json"))
            return

        rows: list[tuple[str, str]] = [
            ("Signed in", "yes" if info.signed_in else "no"),
            ("State directory", str(info.state_directory)),
            ("Public key", info.public_key or "-"),
        ]
        if info.session is not None:
            rows.extend(
                [
                    ("Last country", info.session.country or "-"),
                    ("Last city", info.session.city or "-"),
                    ("Last type", info.session.ip_type or "-"),
                    ("Last exit IP", info.session.exit_ip or "-"),
                ]
            )
        terminal.print_key_values("Mysterium VPN Status", rows)
