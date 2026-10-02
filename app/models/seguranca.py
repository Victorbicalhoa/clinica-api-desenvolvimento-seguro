from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField
from sqlmodel import Field, SQLModel

from app.models.entrada import Entrada


class OrcamentoAuth(SQLModel, table=True):
    chave: str = Field(primary_key=True)
    janela: int
    tentativas: int


class AcaoAuditoria(StrEnum):
    HTTP = "http"
    CRIAR = "consulta.criar"
    ATUALIZAR = "consulta.atualizar"
    EXCLUIR = "consulta.excluir"


class EventoAuditoria(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    instante: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    request_id: str = Field(index=True)
    ator_id: int | None = Field(default=None, index=True)
    acao: AcaoAuditoria
    rota: str
    metodo: str
    recurso_id: int | None = None
    status_http: int
    alerta: bool = False


class AuditoriaRead(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: int
    instante: datetime
    request_id: str
    ator_id: int | None
    acao: AcaoAuditoria
    rota: str
    metodo: str
    recurso_id: int | None
    status_http: int
    alerta: bool


class FiltroAuditoria(Entrada):
    limit: Annotated[int, PydanticField(ge=1, le=100)] = 20
    offset: Annotated[int, PydanticField(ge=0, le=10000)] = 0
    alerta: bool | None = None
