from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field, SecretStr, TypeAdapter, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="forbid",
        hide_input_in_errors=True,
    )

    database_url: SecretStr = Field(
        default=f"sqlite:///{(PROJECT_ROOT / 'data' / 'clinica.db').as_posix()}",
        min_length=1,
    )
    jwt_secret: SecretStr | None = Field(default=None, min_length=32)
    access_token_minutes: int = Field(default=15, ge=1, le=30)
    mfa_simulated: bool = False
    cookie_secure: bool = True
    auth_login_limit: int = Field(default=5, ge=1, le=100)
    auth_mfa_limit: int = Field(default=5, ge=1, le=100)
    auth_ip_limit: int = Field(default=60, ge=1, le=1000)
    auth_window_seconds: int = Field(default=60, ge=1, le=3600)
    login_ip_limit: int = Field(default=20, ge=1, le=1000)
    api_request_limit: int = Field(default=120, ge=1, le=10000)
    hsts_max_age: int = Field(default=31_536_000, ge=1, le=63_072_000)
    max_request_body_bytes: int = Field(default=65_536, ge=1024, le=1_048_576)
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    @field_validator("cors_allow_origins")
    @classmethod
    def explicit_origins(cls, values: list[str]) -> list[str]:
        result = []
        for value in values:
            if "*" in value or any(ord(char) <= 32 for char in value):
                raise ValueError("CORS exige origens explicitas, sem wildcard ou espacos.")
            url = TypeAdapter(AnyHttpUrl).validate_python(value)
            if (
                url.username
                or url.password
                or url.path not in (None, "", "/")
                or url.query is not None
                or url.fragment is not None
            ):
                raise ValueError(
                    "Origem CORS nao pode conter credencial, caminho, query ou fragmento."
                )
            if url.scheme == "http" and url.host not in {"localhost", "127.0.0.1", "[::1]"}:
                raise ValueError("Origens externas devem usar HTTPS; HTTP apenas em loopback.")
            origin = str(url).rstrip("/")
            if origin not in result:
                result.append(origin)
        return result


@lru_cache
def get_settings() -> Settings:
    return Settings()
