from pathlib import Path

from pydantic import SecretStr

from mystgate.core.config import Settings


class SettingsFactory:
    @staticmethod
    def build(
        tmp_path: Path,
        *,
        debug: bool = False,
        proxy_user: str | None = None,
        proxy_pass: str | None = None,
    ) -> Settings:
        """Create an isolated Settings instance rooted under tmp_path."""
        return Settings(
            state_directory=tmp_path / "state",
            log_directory=tmp_path / "logs",
            debug=debug,
            proxy_user=proxy_user,
            proxy_pass=SecretStr(proxy_pass) if proxy_pass is not None else None,
        )
