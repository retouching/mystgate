import json
from pathlib import Path

import httpx
import pytest
import respx
from click.testing import CliRunner
from pydantic import SecretStr

from mystgate.__main__ import Mystgate
from mystgate.core.mysterium import OAuthTokens, TokenStore
from mystgate.core.mysterium.client import API_BASE_URL


class TestCommands:
    @staticmethod
    def configure_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
        """Point CLI environment variables to isolated temporary state and log directories."""
        state_dir = tmp_path / "state"
        log_dir = tmp_path / "logs"
        monkeypatch.setenv("MYSTGATE_STATE_DIRECTORY", str(state_dir))
        monkeypatch.setenv("MYSTGATE_LOG_DIRECTORY", str(log_dir))
        return state_dir

    @respx.mock
    def test_countries_command_json_and_table(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Render countries filtered by IP type as both JSON and plain table."""
        state_dir = self.configure_env(monkeypatch, tmp_path)
        TokenStore(state_dir).save(OAuthTokens(access_token=SecretStr("acc"), refresh_token=SecretStr("ref")))
        respx.get(f"{API_BASE_URL}/connection/config/locations", params={"ip_type": "residential"}).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "country": "FR",
                        "is_available": True,
                        "translations": {"en": "France"},
                        "cities": [{"city": "paris", "is_available": True, "translations": {"en": "Paris"}}],
                    }
                ],
            )
        )

        runner = CliRunner()
        json_result = runner.invoke(Mystgate(), ["countries", "--type", "residential", "--json"])
        assert json_result.exit_code == 0
        payload = json.loads(json_result.output)
        assert payload == [
            {
                "code": "FR",
                "name": "France",
                "cities": ["Paris"],
                "available": True,
                "ip_types": ["residential"],
            }
        ]

        table_result = runner.invoke(Mystgate(), ["countries", "--type", "residential"])
        assert table_result.exit_code == 0
        assert "FR" in table_result.output
        assert "France" in table_result.output
        assert "Paris" in table_result.output
        assert "residential" in table_result.output

    @respx.mock
    def test_connect_stdout_and_status_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Output rendered WireGuard config on stdout and report signed-in status."""
        state_dir = self.configure_env(monkeypatch, tmp_path)
        TokenStore(state_dir).save(OAuthTokens(access_token=SecretStr("acc"), refresh_token=SecretStr("ref")))
        respx.post(f"{API_BASE_URL}/connection/connect").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "s-1",
                    "exit_ip": "198.51.100.7",
                    "ip_type": "residential",
                    "country": "FR",
                    "city": "paris",
                    "limit_exceeded": False,
                    "wg_config": "[Interface]\nPrivateKey = %private_key%\n",
                },
            )
        )

        runner = CliRunner()
        connect_result = runner.invoke(Mystgate(), ["connect", "--country", "FR", "--stdout"])
        assert connect_result.exit_code == 0
        assert "[Interface]" in connect_result.output
        assert "%private_key%" not in connect_result.output

        status_result = runner.invoke(Mystgate(), ["status", "--json"])
        assert status_result.exit_code == 0
        status_data = json.loads(status_result.output)
        assert status_data["signed_in"] is True
        assert status_data["session"]["country"] == "FR"
