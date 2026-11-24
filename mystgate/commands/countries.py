import click

from mystgate.core.config import Settings
from mystgate.core.logging import LogColumn, LogContext, LoggingSession, Terminal
from mystgate.core.mysterium import IPType, MysteriumClient, TokenStore
from mystgate.core.vpn import LocationCatalog


class CountriesCommand(click.Command):
    def __init__(self) -> None:
        """Define the countries CLI command and its filter options."""
        super().__init__(
            name="countries",
            help="List available Mysterium VPN countries with merged cities and IP types.",
            params=[
                click.Option(
                    ["--type", "-t", "ip_type_name"],
                    type=click.Choice(["all", IPType.RESIDENTIAL.value, IPType.HOSTING.value], case_sensitive=False),
                    default="all",
                    show_default=True,
                    help="Filter by IP type (residential, hosting, or all).",
                ),
                click.Option(
                    ["--json", "as_json"],
                    is_flag=True,
                    default=False,
                    help="Output countries as JSON on stdout.",
                ),
            ],
            callback=self.execute,
        )

    @staticmethod
    def execute(ip_type_name: str, as_json: bool) -> None:
        """Fetch and render available countries filtered by IP type."""
        settings = Settings.load()
        terminal = Terminal()
        token_store = TokenStore(settings.state_directory)
        selected_type = None if ip_type_name == "all" else IPType(ip_type_name)

        with (
            LoggingSession(
                settings.log_directory,
                debug=settings.debug,
                secrets=settings.secrets(),
                console_enabled=settings.debug,
            ),
            LogContext.column(LogColumn.API),
            MysteriumClient(settings, token_store=token_store) as client,
            terminal.status("Fetching available countries..."),
        ):
            rows = LocationCatalog(client).list_countries(selected_type)

        if as_json:
            terminal.print_json([row.model_dump(mode="json") for row in rows])
            return

        table_rows = [
            (
                row.code,
                row.name,
                ", ".join(row.cities) if row.cities else "-",
                "yes" if row.available else "no",
                ", ".join(kind.value for kind in row.ip_types),
            )
            for row in rows
        ]
        terminal.print_table(
            f"Mysterium VPN Countries ({len(rows)})",
            ["Code", "Country", "Cities", "Available", "Type"],
            table_rows,
        )
