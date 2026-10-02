from typing import Annotated

from fastapi import APIRouter, Path, Query, Request, Response, status
from sqlmodel import select

from app.auth import consultas_service
from app.auth.dependencies import ProfessionalDep
from app.auth.policies import owned_consulta, scope_consultas
from app.database.session import SessionDep
from app.models.consulta import Consulta, ConsultaRead, ConsultaWrite

router = APIRouter(prefix="/consultas", tags=["Consultas"])
ConsultaId = Annotated[int, Path(gt=0, le=2_147_483_647)]


@router.post("", response_model=ConsultaRead, status_code=status.HTTP_201_CREATED)
def criar_consulta(
    dados: ConsultaWrite,
    response: Response,
    session: SessionDep,
    user: ProfessionalDep,
    request: Request,
) -> Consulta:
    consulta = consultas_service.create(dados, user, session, request)
    response.headers["Location"] = f"/consultas/{consulta.id}"
    return consulta


@router.get("", response_model=list[ConsultaRead])
def listar_consultas(
    session: SessionDep,
    user: ProfessionalDep,
    offset: Annotated[int, Query(ge=0, le=2_147_483_647)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Consulta]:
    statement = (
        scope_consultas(select(Consulta), user).order_by(Consulta.id).offset(offset).limit(limit)
    )
    return list(session.exec(statement).all())


@router.get("/{consulta_id}", response_model=ConsultaRead)
def obter_consulta(consulta_id: ConsultaId, session: SessionDep, user: ProfessionalDep) -> Consulta:
    return owned_consulta(consulta_id, session, user)


@router.put("/{consulta_id}", response_model=ConsultaRead)
def atualizar_consulta(
    consulta_id: ConsultaId,
    dados: ConsultaWrite,
    session: SessionDep,
    user: ProfessionalDep,
    request: Request,
) -> Consulta:
    return consultas_service.replace(consulta_id, dados, user, session, request)


@router.delete("/{consulta_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_consulta(
    consulta_id: ConsultaId, session: SessionDep, user: ProfessionalDep, request: Request
) -> Response:
    consultas_service.remove(consulta_id, user, session, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
