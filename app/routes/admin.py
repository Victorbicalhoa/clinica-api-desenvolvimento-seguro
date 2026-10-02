from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlmodel import select

from app.auth.dependencies import SessionDep, admin_user
from app.models.seguranca import AuditoriaRead, EventoAuditoria, FiltroAuditoria
from app.models.usuario import Usuario

router = APIRouter(prefix="/admin", tags=["Administracao"])


class AdminRead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
    mfa_verified: bool


@router.get("/painel", response_model=AdminRead)
def painel(user: Annotated[Usuario, Depends(admin_user)]) -> AdminRead:
    return AdminRead(message="Acesso administrativo autorizado.", mfa_verified=True)


@router.get("/auditoria", response_model=list[AuditoriaRead])
def auditoria(
    user: Annotated[Usuario, Depends(admin_user)],
    session: SessionDep,
    filters: Annotated[FiltroAuditoria, Query()],
):
    statement = select(EventoAuditoria)
    if filters.alerta is not None:
        statement = statement.where(EventoAuditoria.alerta == filters.alerta)
    return list(
        session.exec(
            statement.order_by(EventoAuditoria.id.desc())
            .offset(filters.offset)
            .limit(filters.limit)
        ).all()
    )
