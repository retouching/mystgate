from pydantic import BaseModel, ConfigDict, SecretStr


class KeyPair(BaseModel):
    model_config = ConfigDict(frozen=True)

    private_key: SecretStr
    public_key: str
