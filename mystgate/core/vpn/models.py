from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from mystgate.core.mysterium import IPType, SessionMetadata


class ConnectOptions(BaseModel):
    model_config = ConfigDict(frozen=True)

    country: str
    ip_type: IPType
    city: str | None = None
    output: Path | None = None
    overwrite: bool = False
    stdout_only: bool = False
    from_config: Path | None = None
    new_key: bool = False


class CountryRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    name: str
    cities: list[str] = Field(default_factory=list)
    available: bool
    ip_types: list[IPType] = Field(default_factory=list)


class ConnectResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    metadata: SessionMetadata
    config_path: Path | None
    rendered_config: str
    public_key: str


class LocalStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    signed_in: bool
    public_key: str | None
    session: SessionMetadata | None
    state_directory: Path
