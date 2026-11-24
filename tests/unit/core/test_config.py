import pytest

from mystgate.core.config import Settings
from mystgate.core.exceptions import ConfigurationError
from tests.constants import ROOT


class TestSettings:
    def test_load_defaults(self) -> None:
        """Load default settings when no environment variables are set."""
        settings = Settings.load()
        assert str(settings.state_directory) == ".mystgate/session"
        assert str(settings.log_directory) == ".mystgate/logs"
        assert settings.debug is False
        assert settings.proxy_user is None
        assert settings.proxy_pass is None
        assert settings.secrets() == ()

    def test_exposes_proxy_password_only_via_secrets(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Expose proxy_pass through secrets() while keeping repr redacted."""
        monkeypatch.setenv("MYSTGATE_PROXY_PASS", "super-secret-pass")

        settings = Settings.load()
        assert settings.secrets() == ("super-secret-pass",)
        assert "super-secret-pass" not in repr(settings)

    def test_rejects_invalid_debug_boolean(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Raise ConfigurationError when MYSTGATE_DEBUG is not a valid boolean."""
        monkeypatch.setenv("MYSTGATE_DEBUG", "not-a-bool")

        with pytest.raises(ConfigurationError) as info:
            Settings.load()
        assert info.value.exit_code == 2

    def test_env_example_matches_settings_fields(self) -> None:
        """Verify .env.example lists every Settings field and leaves secrets empty."""
        lines = [
            line.strip()
            for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        parsed = dict(line.split("=", 1) for line in lines)
        expected = {f"MYSTGATE_{name.upper()}" for name in Settings.model_fields}
        assert set(parsed) == expected
        assert parsed["MYSTGATE_PROXY_PASS"] == ""
