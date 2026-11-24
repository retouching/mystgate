import io
import json

from mystgate.core.exceptions import WireGuardError
from mystgate.core.logging import Terminal


class TestTerminal:
    def test_separates_stdout_and_stderr(self) -> None:
        """Send primary data to stdout and errors to stderr."""
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        terminal = Terminal(stdout=out_buf, stderr=err_buf)

        terminal.print_json({"country": "FR"})
        terminal.print_error(WireGuardError("WireGuard: failed"))

        assert json.loads(out_buf.getvalue()) == {"country": "FR"}
        assert "WireGuard: failed" in err_buf.getvalue()
        assert "WireGuard: failed" not in out_buf.getvalue()

    def test_renders_table(self) -> None:
        """Render structured rows into an aligned plain table on stdout."""
        out_buf = io.StringIO()
        terminal = Terminal(stdout=out_buf, stderr=io.StringIO())
        terminal.print_table("Countries", ["Code", "Type"], [("FR", "residential")])
        output = out_buf.getvalue()
        assert "Code" in output
        assert "FR" in output
        assert "residential" in output
