from fastapi import HTTPException, Request
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.auth.audit import mutation
from app.auth.policies import authorize_write, owned_consulta, scope_consultas
from app.models.consulta import Consulta, ConsultaWrite, StatusConsulta
from app.models.seguranca import AcaoAuditoria
from app.models.usuario import Usuario


def conflict(exc: IntegrityError) -> HTTPException:
    # Nao expor SQL, parametros, dados clinicos ou detalhes de constraint.
    return HTTPException(409, "Conflito ao persistir consulta.")


def create(data: ConsultaWrite, user: Usuario, session: Session, request: Request) -> Consulta:
    authorize_write(data, user, session)
    if data.status != StatusConsulta.AGENDADA:
        raise HTTPException(422, "Nova consulta deve iniciar como agendada.")
    record = Consulta(**data.model_dump())
    try:
        session.add(record)
        session.flush()
        mutation(session, request, AcaoAuditoria.CRIAR, 201, record.id)
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise conflict(exc) from exc
    request.state.audit_written = True
    session.refresh(record)
    return record


def replace(
    consulta_id: int, data: ConsultaWrite, user: Usuario, session: Session, request: Request
) -> Consulta:
    record = owned_consulta(consulta_id, session, user)
    authorize_write(data, user, session)
    if record.status != StatusConsulta.AGENDADA and any(
        getattr(record, key) != value for key, value in data.model_dump().items()
    ):
        raise HTTPException(409, "Consulta finalizada nao pode ser alterada.")
    statement = (
        scope_consultas(update(Consulta), user)
        .where(
            Consulta.id == consulta_id,
            Consulta.status == record.status,
        )
        .values(**data.model_dump())
        .returning(Consulta.id)
    )
    try:
        changed = session.exec(statement).first()
        if changed is None:
            session.rollback()
            raise HTTPException(409, "Consulta alterada por outra operacao.")
        mutation(session, request, AcaoAuditoria.ATUALIZAR, 200, consulta_id)
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise conflict(exc) from exc
    request.state.audit_written = True
    session.refresh(record)
    return record


def remove(consulta_id: int, user: Usuario, session: Session, request: Request) -> None:
    record = owned_consulta(consulta_id, session, user)
    try:
        session.delete(record)
        mutation(session, request, AcaoAuditoria.EXCLUIR, 204, consulta_id)
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise conflict(exc) from exc
    request.state.audit_written = True
