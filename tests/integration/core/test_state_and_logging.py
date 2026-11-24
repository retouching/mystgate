import logging
import stat
from pathlib import Path

from pydantic import SecretStr

from mystgate.core.config import Settings
from mystgate.core.logging import LogColumn, LogContext, LoggingSession, LogMarker
from mystgate.core.mysterium import OAuthTokens, SessionMetadata, TokenStore
from mystgate.core.vpn import StateStore
from mystgate.core.wireguard import ConfigWriter, KeyGenerator
from tests.support import JSONLog


class TestStateAndLoggingIntegration:
    def test_dotenv_settings_private_files_and_redacted_json_logs(self, tmp_path: Path) -> None:
        """Load .env on disk, write 0600 state and WireGuard files, and verify redacted JSON logs."""
        state_dir = tmp_path / "state"
        log_dir = tmp_path / "logs"
        (tmp_path / ".env").write_text(
            f"MYSTGATE_STATE_DIRECTORY={state_dir}\n"
            f"MYSTGATE_LOG_DIRECTORY={log_dir}\n"
            "MYSTGATE_DEBUG=true\n"
            "MYSTGATE_PROXY_USER=alice\n"
            "MYSTGATE_PROXY_PASS=integration-secret-pass\n",
            encoding="utf-8",
        )

        settings = Settings.load()
        assert settings.state_directory == state_dir
        assert settings.log_directory == log_dir

        token_store = TokenStore(settings.state_directory)
        token_store.save(OAuthTokens(access_token=SecretStr("acc-int"), refresh_token=SecretStr("ref-int")))
        first_fp = token_store.fingerprint()
        assert first_fp is not None
        assert stat.S_IMODE(token_store.path.stat().st_mode) == 0o600

        state_store = StateStore(settings.state_directory)
        keypair = state_store.load_or_create_keypair()
        state_store.save_session(SessionMetadata(country="FR", ip_type="residential", exit_ip="198.51.100.1"))
        wg_path = ConfigWriter.write_template(
            "[Interface]\nPrivateKey = %private_key%\n",
            keypair,
            state_store.wg_config_path,
            overwrite=True,
        )
        assert stat.S_IMODE(wg_path.stat().st_mode) == 0o600
        assert KeyGenerator.from_config_file(wg_path).public_key == keypair.public_key

        with (
            LoggingSession(settings.log_directory, debug=True, secrets=settings.secrets(), console_enabled=False),
            LogContext.column(LogColumn.WIREGUARD),
        ):
            logging.getLogger("mystgate.integration").info(
                "%s Ready proxy=http://alice:integration-secret-pass@127.0.0.1:8080",
                LogMarker.DONE.value,
            )

        entries = JSONLog.read(settings.log_directory)
        assert len(entries) == 1
        assert "integration-secret-pass" not in str(entries[0]["message"])
        assert "<redacted>" in str(entries[0]["message"])
