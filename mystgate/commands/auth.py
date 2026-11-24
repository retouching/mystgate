import click

from mystgate.core.config import Settings
from mystgate.core.logging import LogColumn, LogContext, LoggingSession, Terminal
from mystgate.core.mysterium import MysteriumClient, TokenStore
from mystgate.core.vpn import Authenticator


class AuthCommand(click.Command):
    def __init__(self) -> None:
        """Define the auth CLI command."""
        super().__init__(
            name="auth",
            help="Sign in to Mysterium VPN via browser approval.",
            callback=self.execute,
        )

    @staticmethod
    def execute() -> None:
        """Run browser-approval OAuth authentication and store tokens securely."""
        settings = Settings.load()
        terminal = Terminal()
        token_store = TokenStore(settings.state_directory)

        with (
            LoggingSession(
                settings.log_directory,
                debug=settings.debug,
                secrets=settings.secrets(),
                console_enabled=settings.debug,
            ),
            LogContext.column(LogColumn.API),
            MysteriumClient(settings, token_store=token_store) as client,
        ):
            authenticator = Authenticator(client, token_store)
            activation_id, approve_url = authenticator.start()
            terminal.print_panel(
                f"Open this URL in your browser, sign in, and approve within 5 minutes:\n\n{approve_url}",
                title="Mysterium VPN Sign In",
            )
            with terminal.status("Waiting for browser approval..."):
                authenticator.wait_for_tokens(activation_id)

        terminal.print_info(f"Signed in. Tokens saved to {token_store.path}")
