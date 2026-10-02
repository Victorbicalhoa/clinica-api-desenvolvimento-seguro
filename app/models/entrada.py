from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

USERNAME_PATTERN = r"^[A-Za-z0-9._-]{1,100}$"
Username = Annotated[str, Field(pattern=USERNAME_PATTERN, strict=True)]


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginForm(Entrada):
    grant_type: Literal["password"]
    username: Username
    password: SecretStr
    scope: Literal[""] = ""
    # Campos padrao enviados pelo Swagger; clientes M2M nao sao suportados aqui.
    client_id: Literal[""] = ""
    client_secret: Literal[""] = ""

    @field_validator("password")
    @classmethod
    def password_size(cls, value: SecretStr) -> SecretStr:
        if not 1 <= len(value.get_secret_value().encode("utf-8")) <= 72:
            raise ValueError("Senha fora do tamanho permitido.")
        return value


class CorpoVazio(Entrada):
    pass
