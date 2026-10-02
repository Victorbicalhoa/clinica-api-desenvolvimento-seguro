import re
from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import ValidationError
from sqlalchemy import exists
from sqlmodel import select
from starlette.concurrency import run_in_threadpool

from app.auth.integracao import issue_machine_token
from app.auth.limits import consume
from app.auth.security import verify_password
from app.database.session import SessionDep
from app.models.consulta import Consulta, StatusConsulta
from app.models.entrada import USERNAME_PATTERN
from app.models.integracao import (
    SCOPE_AVAILABILITY,
    ClientCredentialsForm,
    ClienteIntegracao,
    ClienteProfissional,
    HorarioRead,
    MachineTokenRead,
    SlotOferta,
)
from app.models.usuario import Papel, Usuario

router = APIRouter(prefix="/integracoes", tags=["Laboratorio M2M"])
basic = HTTPBasic(auto_error=False, scheme_name="ClientBasic")


def oauth_error(error: str, status=400):
    headers = {"Cache-Control": "no-store", "Pragma": "no-cache"}
    if status == 401:
        headers["WWW-Authenticate"] = 'Basic realm="integracoes"'
    return JSONResponse({"error": error}, status_code=status, headers=headers)


@router.post("/token", response_model=MachineTokenRead)
async def machine_token(
    request: Request,
    session: SessionDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(basic)],
):
    if (
        request.query_params
        or request.headers.get("content-type", "").split(";")[0].lower()
        != "application/x-www-form-urlencoded"
        or len(request.headers.getlist("Authorization")) != 1
    ):
        return oauth_error("invalid_request")
    form = await request.form()
    if any(len(form.getlist(key)) != 1 for key in form):
        return oauth_error("invalid_request")
    try:
        data = ClientCredentialsForm.model_validate(dict(form))
    except ValidationError:
        return oauth_error("invalid_request")
    return await run_in_threadpool(grant_machine, request, session, credentials, data)


def grant_machine(request, session, credentials, data):
    # SQLite e bcrypt fora do event loop; nenhuma operacao concorrente na Session.
    if credentials is None or not re.fullmatch(USERNAME_PATTERN, credentials.username):
        return oauth_error("invalid_client", 401)
    consume(session, "machine-token", credentials.username, 5, 60, request.app.state.rate_clock())
    client = session.get(ClienteIntegracao, credentials.username)
    # Mesmo trabalho bcrypt para cliente inexistente; nunca revelar qual ID existe.
    hashed = client.secret_hash if client else request.app.state.dummy_hash
    secret = credentials.password if credentials else ""
    valid = verify_password(secret, hashed)
    if not valid or client is None or not client.ativo:
        return oauth_error("invalid_client", 401)
    request.state.machine_id = client.client_id
    requested = set(data.scope.split())
    if requested != {SCOPE_AVAILABILITY} or not requested <= set(client.scopes.split()):
        return oauth_error("invalid_scope")
    return issue_machine_token(client, SCOPE_AVAILABILITY, request)


@router.get("/disponibilidade", response_model=list[HorarioRead])
def availability(
    request: Request,
    session: SessionDep,
    dia: date,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    client = getattr(request.state, "machine_identity", None)
    if client is None:
        raise HTTPException(401, "Identidade M2M requerida.")
    if dia == date.max or set(request.query_params) - {"dia", "limit", "offset"}:
        raise HTTPException(422, "Parametros invalidos.")
    if any(len(request.query_params.getlist(key)) != 1 for key in request.query_params):
        raise HTTPException(422, "Parametros duplicados.")
    start = datetime.combine(dia, time.min, tzinfo=UTC)
    occupied = exists().where(
        Consulta.profissional_id == SlotOferta.profissional_id,
        Consulta.data_hora == SlotOferta.inicio,
        Consulta.status != StatusConsulta.CANCELADA,
    )
    query = (
        select(SlotOferta)
        .join(
            ClienteProfissional, ClienteProfissional.profissional_id == SlotOferta.profissional_id
        )
        .join(Usuario, Usuario.profissional_id == SlotOferta.profissional_id)
        .where(
            ClienteProfissional.client_id == client.client_id,
            Usuario.ativo.is_(True),
            Usuario.papel == Papel.PROFISSIONAL,
            SlotOferta.inicio >= start,
            SlotOferta.inicio < start + timedelta(days=1),
            SlotOferta.inicio > datetime.now(UTC),
            ~occupied,
        )
        .order_by(SlotOferta.inicio, SlotOferta.profissional_id)
        .offset(offset)
        .limit(limit)
    )
    return [
        HorarioRead(profissional_id=item.profissional_id, inicio=item.inicio)
        for item in session.exec(query).all()
    ]
