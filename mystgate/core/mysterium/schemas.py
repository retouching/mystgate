from pydantic import BaseModel, ConfigDict, Field, SecretStr


class OAuthTokens(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    access_token: SecretStr
    refresh_token: SecretStr


class ActivationStatus(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str
    valid: bool
    token: OAuthTokens | None = None


class CityLocation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    city: str
    total: int = 0
    translations: dict[str, str] = Field(default_factory=dict)
    is_available: bool = True

    def display_name(self, language: str = "en") -> str:
        """Return the translated city name or fall back to its identifier."""
        return self.translations.get(language) or self.translations.get("en") or self.city


class CountryLocation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    country: str
    total: int = 0
    translations: dict[str, str] = Field(default_factory=dict)
    is_available: bool = True
    cities: list[CityLocation] = Field(default_factory=list)

    def display_name(self, language: str = "en") -> str:
        """Return the translated country name or fall back to its ISO code."""
        return self.translations.get(language) or self.translations.get("en") or self.country


class SessionMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str | None = None
    exit_ip: str | None = None
    ip_type: str | None = None
    country: str | None = None
    city: str | None = None
    limit_exceeded: bool = False


class ConnectionResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str | None = None
    exit_ip: str | None = None
    ip_type: str | None = None
    country: str | None = None
    city: str | None = None
    limit_exceeded: bool = False
    wg_config: str = ""

    def metadata(self) -> SessionMetadata:
        """Extract session metadata without the WireGuard configuration template."""
        return SessionMetadata(
            id=self.id,
            exit_ip=self.exit_ip,
            ip_type=self.ip_type,
            country=self.country,
            city=self.city,
            limit_exceeded=self.limit_exceeded,
        )
