from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime
from pydantic import Field as PydanticField
from sqlmodel import Field, SQLModel

from app.models.consulta import IdRecurso
from app.models.entrada import Entrada

SCOPE_AVAILABILITY = "disponibilidade:read"


class ClienteIntegracao(SQLModel, table=True):
    client_id: str = Field(primary_key=True, max_length=100)
    secret_hash: str
    ativo: bool = True
    scopes: str = SCOPE_AVAILABILITY
    token_version: int = 1


class ClienteProfissional(SQLModel, table=True):
    client_id: str = Field(foreign_key="clienteintegracao.client_id", primary_key=True)
    profissional_id: int = Field(primary_key=True)


class SlotOferta(SQLModel, table=True):
    profissional_id: int = Field(primary_key=True)
    inicio: datetime = Field(primary_key=True)


class EventoIntegracao(SQLModel, table=True):
    request_id: str = Field(primary_key=True)
    client_id: str
    rota: str
    status_http: int


class ClientCredentialsForm(Entrada):
    grant_type: Literal["client_credentials"]
    scope: str = PydanticField(default=SCOPE_AVAILABILITY, max_length=200, strict=True)


class MachineTokenRead(Entrada):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = 300
    scope: str


class HorarioRead(Entrada):
    profissional_id: IdRecurso
    inicio: AwareDatetime
