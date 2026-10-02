from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Index
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from app.models.entrada import Entrada


class StatusConsulta(StrEnum):
    AGENDADA = "agendada"
    CANCELADA = "cancelada"
    REALIZADA = "realizada"


IdRecurso = Annotated[int, Field(gt=0, strict=True, le=2_147_483_647)]


class ConsultaWrite(Entrada):
    """Contrato para criacao e substituicao completa (PUT)."""

    model_config = ConfigDict(extra="forbid")

    paciente_id: IdRecurso
    profissional_id: IdRecurso
    data_hora: AwareDatetime
    status: StatusConsulta = StatusConsulta.AGENDADA
    observacao: str = Field(default="", max_length=500, strict=True)

    @field_validator("data_hora", mode="before")
    @classmethod
    def exigir_data_iso(cls, value: object) -> object:
        if not isinstance(value, (str, datetime)):
            raise ValueError("Informe data/hora ISO 8601 com fuso horario.")
        return value

    @field_validator("data_hora")
    @classmethod
    def normalizar_utc(cls, value: datetime) -> datetime:
        try:
            return value.astimezone(UTC)
        except OverflowError as exc:
            raise ValueError("Data/hora fora do intervalo suportado em UTC.") from exc


class ConsultaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: IdRecurso
    paciente_id: IdRecurso
    profissional_id: IdRecurso
    data_hora: AwareDatetime
    status: StatusConsulta
    observacao: str


class Consulta(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    paciente_id: int = SQLField(index=True)
    profissional_id: int = SQLField(index=True)
    data_hora: datetime
    status: StatusConsulta = SQLField(default=StatusConsulta.AGENDADA)

    observacao: str = SQLField(default="", max_length=500)
    criado_em: datetime = SQLField(default_factory=lambda: datetime.now(UTC))
    referencia_interna: str = SQLField(default_factory=lambda: str(uuid4()), max_length=36)


SLOT_INDEX = Index(
    "uq_consulta_profissional_instante_ativa",
    Consulta.profissional_id,
    Consulta.data_hora,
    unique=True,
    sqlite_where=Consulta.status != StatusConsulta.CANCELADA,
)
