from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.consulta import Consulta, ConsultaWrite
from app.models.usuario import Papel, Usuario, VinculoPaciente


def scope_consultas(statement, user: Usuario):
    # Um unico predicado protege consulta individual, listas e agenda.
    if user.papel != Papel.PROFISSIONAL or user.profissional_id is None:
        raise HTTPException(403, "Acesso clinico requer profissional vinculado.")
    patients = select(VinculoPaciente.paciente_id).where(VinculoPaciente.usuario_id == user.id)
    return statement.where(
        Consulta.profissional_id == user.profissional_id,
        Consulta.paciente_id.in_(patients),
    )


def owned_consulta(consulta_id: int, session: Session, user: Usuario) -> Consulta:
    record = session.exec(
        scope_consultas(select(Consulta).where(Consulta.id == consulta_id), user)
    ).first()
    if record is None:
        raise HTTPException(404, "Consulta nao encontrada.")
    return record


def authorize_write(data: ConsultaWrite, user: Usuario, session: Session) -> None:
    if (
        data.profissional_id != user.profissional_id
        or session.get(VinculoPaciente, (user.id, data.paciente_id)) is None
    ):
        raise HTTPException(403, "Consulta fora dos vinculos autorizados.")
