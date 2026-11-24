from __future__ import annotations

from importlib.metadata import version
from typing import TYPE_CHECKING

import click

from mystgate.commands import (
    AuthCommand,
    ConnectCommand,
    CountriesCommand,
    DisconnectCommand,
    StatusCommand,
)
from mystgate.core.exceptions import MystgateError
from mystgate.core.logging import Terminal
from mystgate.core.utils import message

if TYPE_CHECKING:
    from collections.abc import Sequence


class Mystgate(click.Group):
    def __init__(self, *, commands: Sequence[click.Command] | None = None) -> None:
        """Build the root CLI command group."""
        super().__init__(
            name="mystgate",
            help="Generate and manage WireGuard configurations from the Mysterium VPN API.",
            params=[
                click.Option(
                    ["--version", "-V"],
                    is_flag=True,
                    is_eager=True,
                    expose_value=False,
                    callback=self.show_version,
                    help="Show the application version and exit.",
                )
            ],
        )
        registered = (
            commands
            if commands is not None
            else (
                AuthCommand(),
                CountriesCommand(),
                ConnectCommand(),
                DisconnectCommand(),
                StatusCommand(),
            )
        )
        for command in registered:
            self.add_command(command)

    @staticmethod
    def show_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
        """Print the installed package version and exit."""
        del param
        if not value or ctx.resilient_parsing:
            return
        Terminal().print_text(f"mystgate {version('mystgate')}")
        ctx.exit()

    @classmethod
    def run(
        cls,
        arguments: Sequence[str] | None = None,
        *,
        commands: Sequence[click.Command] | None = None,
    ) -> int:
        """Execute the CLI and translate failures into deterministic exit codes."""
        terminal = Terminal()
        try:
            cls(commands=commands).main(
                args=list(arguments) if arguments is not None else None,
                prog_name="mystgate",
                standalone_mode=False,
            )
        except MystgateError as error:
            terminal.print_error(error)
            return error.exit_code
        except click.ClickException as error:
            error.show()
            return error.exit_code
        except click.Abort, KeyboardInterrupt:
            terminal.print_info(message("Command", "interrupted"))
            return 130
        return 0


if __name__ == "__main__":
    raise SystemExit(Mystgate.run())
