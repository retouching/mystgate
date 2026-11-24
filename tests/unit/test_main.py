import inspect

import click
from click.testing import CliRunner

from mystgate.__main__ import Mystgate
from mystgate.core.exceptions import WireGuardError


class FailingCommand(click.Command):
    def __init__(self) -> None:
        """Build a dummy command that always raises WireGuardError."""
        super().__init__(name="fail", callback=self.execute)

    @staticmethod
    def execute() -> None:
        """Raise WireGuardError to verify exit-code translation."""
        raise WireGuardError("WireGuard: forced failure")


class InterruptingCommand(click.Command):
    def __init__(self) -> None:
        """Build a dummy command that simulates KeyboardInterrupt."""
        super().__init__(name="interrupt", callback=self.execute)

    @staticmethod
    def execute() -> None:
        """Raise KeyboardInterrupt to verify exit code 130."""
        raise KeyboardInterrupt


class TestMystgate:
    def test_help_and_version(self) -> None:
        """Expose all subcommands in --help and print package version with --version."""
        runner = CliRunner()
        help_result = runner.invoke(Mystgate(), ["--help"])
        assert help_result.exit_code == 0
        for command_name in ("auth", "countries", "connect", "disconnect", "status"):
            assert command_name in help_result.output

        version_result = runner.invoke(Mystgate(), ["--version"])
        assert version_result.exit_code == 0
        assert "mystgate" in version_result.output

    def test_run_translates_domain_error_exit_code(self) -> None:
        """Return the domain exception's deterministic exit code from Mystgate.run."""
        code = Mystgate.run(["fail"], commands=[FailingCommand()])
        assert code == WireGuardError.exit_code

    def test_run_translates_keyboard_interrupt_to_130(self) -> None:
        """Return exit code 130 when interrupted by KeyboardInterrupt."""
        code = Mystgate.run(["interrupt"], commands=[InterruptingCommand()])
        assert code == 130

    def test_every_command_option_matches_callback_signature(self) -> None:
        """Verify every Click option name matches its command callback parameters."""
        root = Mystgate()
        for name, command in root.commands.items():
            assert command.callback is not None, f"command {name} has no callback"
            expected = set(inspect.signature(command.callback).parameters)
            exposed = {param.name for param in command.params if param.expose_value and param.name is not None}
            assert exposed == expected, f"command {name}: exposed {exposed} != signature {expected}"
