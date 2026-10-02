import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import update
from sqlmodel import select

from app.auth.dependencies import SessionDep, UserDep, current_session
from app.auth.limits import consume
from app.auth.security import issue_token, unauthorized, verify_password
from app.auth.validation import empty_body, login_form
from app.models.entrada import LoginForm
from app.models.usuario import (
    DesafioMFA,
    DesafioRead,
    MFAWrite,
    Papel,
    Sessao,
    TokenRead,
    Usuario,
)

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


def otp_digest(request: Request, challenge: str, code: str) -> str:
    return hmac.new(
        request.app.state.jwt_secret.encode(),
        f"{challenge}:{code}".encode(),
        hashlib.sha256,
    ).hexdigest()


def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


@router.post("/token", response_model=TokenRead | DesafioRead)
def login(
    request: Request,
    response: Response,
    session: SessionDep,
    form: Annotated[LoginForm, Depends(login_form)],
):
    no_store(response)
    settings = request.app.state.settings
    consume(
        session,
        "login",
        form.username.lower(),
        settings.auth_login_limit,
        settings.auth_window_seconds,
        request.app.state.rate_clock(),
    )
    user = session.exec(select(Usuario).where(Usuario.username == form.username)).first()
    hashed = user.password_hash if user else request.app.state.dummy_hash
    valid = verify_password(form.password.get_secret_value(), hashed)
    if not valid or user is None or not user.ativo:
        raise unauthorized()
    if user.papel == Papel.ADMIN:
        if not request.app.state.settings.mfa_simulated:
            raise HTTPException(
                503,
                "Canal MFA simulado desativado; acesso administrativo indisponivel.",
            )
        challenge = secrets.token_hex(16)
        code = f"{secrets.randbelow(1_000_000):06}"
        session.add(
            DesafioMFA(
                id=challenge,
                usuario_id=user.id,
                codigo_hash=otp_digest(request, challenge, code),
                expira_em=datetime.now(UTC) + timedelta(seconds=120),
            )
        )
        session.commit()
        # Adaptador didatico: substituido por coletor em testes; nunca retorna OTP na API.
        request.app.state.mfa_sender(challenge, code)
        response.status_code = 202
        return DesafioRead(challenge_id=challenge)
    result = issue_token(user, session, request)
    request.state.audit_actor = user.id
    return result


@router.post("/mfa", response_model=TokenRead)
def confirm_mfa(data: MFAWrite, request: Request, response: Response, session: SessionDep):
    no_store(response)
    if not request.app.state.settings.mfa_simulated:
        raise unauthorized()
    known = session.get(DesafioMFA, data.challenge_id)
    if known is not None:
        settings = request.app.state.settings
        consume(
            session,
            "mfa",
            str(known.usuario_id),
            settings.auth_mfa_limit,
            settings.auth_window_seconds,
            request.app.state.rate_clock(),
        )
    # Claim de uma tentativa por UPDATE condicional: evita replay e corrida read-then-write.
    statement = (
        update(DesafioMFA)
        .where(
            DesafioMFA.id == data.challenge_id,
            DesafioMFA.consumido.is_(False),
            DesafioMFA.tentativas < 5,
            DesafioMFA.expira_em > datetime.now(UTC),
        )
        .values(tentativas=DesafioMFA.tentativas + 1)
        .returning(DesafioMFA.codigo_hash, DesafioMFA.usuario_id)
    )
    claimed = session.exec(statement).first()
    if claimed is None:
        session.rollback()
        raise unauthorized()
    if not hmac.compare_digest(
        claimed.codigo_hash, otp_digest(request, data.challenge_id, data.code)
    ):
        session.commit()
        raise unauthorized()
    session.exec(
        update(DesafioMFA).where(DesafioMFA.id == data.challenge_id).values(consumido=True)
    )
    user = session.get(Usuario, claimed.usuario_id)
    if user is None or not user.ativo or user.papel != Papel.ADMIN:
        session.commit()
        raise unauthorized()
    # issue_token confirma consumo e sessao na mesma transacao.
    result = issue_token(user, session, request, mfa=True)
    request.state.audit_actor = user.id
    return result


@router.post("/logout", status_code=204, dependencies=[Depends(empty_body)])
def logout(
    response: Response,
    session: SessionDep,
    identity: Annotated[tuple[Usuario, Sessao], Depends(current_session)],
):
    record = identity[1]
    record.revogada = True
    session.add(record)
    session.commit()
    response.delete_cookie("agenda_session", path="/agenda")
    no_store(response)


@router.post("/browser-session", status_code=204, dependencies=[Depends(empty_body)])
def browser_session(request: Request, response: Response, user: UserDep):
    # Apenas Bearer autentica este POST; cookie so e aceito no GET /agenda.
    if user.papel not in (Papel.PROFISSIONAL, Papel.RECEPCIONISTA):
        raise HTTPException(403, "Papel sem acesso a agenda.")
    token = request.headers["Authorization"].split()[1]
    response.set_cookie(
        "agenda_session",
        token,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="strict",
        path="/agenda",
        max_age=request.app.state.settings.access_token_minutes * 60,
    )
    no_store(response)
