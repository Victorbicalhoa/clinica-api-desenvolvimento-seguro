from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField
from sqlmodel import Field, SQLModel

from app.models.entrada import Entrada


class Papel(StrEnum):
    PROFISSIONAL = "profissional"
    RECEPCIONISTA = "recepcionista"
    ADMIN = "administrador"


class Usuario(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    papel: Papel
    profissional_id: int | None = Field(default=None, unique=True)
    ativo: bool = True


class VinculoPaciente(SQLModel, table=True):
    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
    paciente_id: int = Field(primary_key=True)


class Sessao(SQLModel, table=True):
    jti: str = Field(primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    expira_em: datetime
    mfa: bool = False
    revogada: bool = False


class DesafioMFA(SQLModel, table=True):
    id: str = Field(primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    codigo_hash: str
    expira_em: datetime
    tentativas: int = 0
    consumido: bool = False


class TokenRead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class DesafioRead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    challenge_id: str
    mfa_required: bool = True
    expires_in: int = 120


class MFAWrite(Entrada):
    model_config = ConfigDict(extra="forbid")
    challenge_id: str = PydanticField(pattern=r"^[a-f0-9]{32}$", strict=True)
    code: str = PydanticField(pattern=r"^[0-9]{6}$", strict=True)
