import json

from tests.e2e.e2e_test import E2ETest


class TestCommands(E2ETest):
    def test_cli_help_version_status_and_gateway_tools_in_container(self) -> None:
        """Verify mystgate CLI and Gluetun-like gateway tools (wg, iptables, pproxy) exist in container."""
        help_res = self.stack.exec_cli("--help")
        assert "countries" in help_res.stdout
        assert "connect" in help_res.stdout

        version_res = self.stack.exec_cli("--version")
        assert "mystgate" in version_res.stdout

        status_res = self.stack.exec_cli("status", "--json")
        payload = json.loads(status_res.stdout)
        assert payload["signed_in"] is False
        assert payload["state_directory"] == "/data/state"

        assert self.stack.exec_raw("wg", "--version").returncode == 0
        assert self.stack.exec_raw("iptables", "--version").returncode == 0
        assert self.stack.exec_raw("pproxy", "--version").returncode == 0
