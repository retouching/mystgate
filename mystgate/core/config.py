from pathlib import Path
from typing import ClassVar, Self

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from mystgate.core.exceptions import ConfigurationError
from mystgate.core.utils import message

DEFAULT_STATE_DIRECTORY: Path = Path(".mystgate") / "session"
DEFAULT_LOG_DIRECTORY: Path = Path(".mystgate") / "logs"


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="MYSTGATE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    state_directory: Path = Field(default=DEFAULT_STATE_DIRECTORY)
    log_directory: Path = Field(default=DEFAULT_LOG_DIRECTORY)
    debug: bool = False
    proxy_user: str | None = None
    proxy_pass: SecretStr | None = None

    @field_validator("state_directory", mode="before")
    @classmethod
    def default_state_directory(cls, value: object) -> object:
        """Fallback to the default state directory when the variable is empty."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return DEFAULT_STATE_DIRECTORY
        if isinstance(value, str):
            return Path(value).expanduser()
        return value

    @field_validator("log_directory", mode="before")
    @classmethod
    def default_log_directory(cls, value: object) -> object:
        """Fallback to the default log directory when the variable is empty."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return DEFAULT_LOG_DIRECTORY
        if isinstance(value, str):
            return Path(value).expanduser()
        return value

    @field_validator("proxy_user", mode="before")
    @classmethod
    def normalize_proxy_user(cls, value: object) -> object:
        """Convert empty proxy user strings to None."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("proxy_pass", mode="before")
    @classmethod
    def normalize_proxy_pass(cls, value: object) -> object:
        """Convert empty proxy password strings to None."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    def secrets(self) -> tuple[str, ...]:
        """Return all non-empty secret values configured in settings."""
        if self.proxy_pass is None:
            return ()
        value = self.proxy_pass.get_secret_value()
        return (value,) if value else ()

    @classmethod
    def load(cls) -> Self:
        """Load and validate settings from environment variables and .env."""
        try:
            return cls()
        except ValidationError as error:
            causes = [
                f"MYSTGATE_{'_'.join(str(part) for part in item['loc']).upper()}: {item['msg']}"
                for item in error.errors()
            ]
            raise ConfigurationError(message("Configuration", "invalid", *causes)) from error
