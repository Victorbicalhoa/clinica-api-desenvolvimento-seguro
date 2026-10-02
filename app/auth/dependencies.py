from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from app.auth.security import unauthorized
from app.database.session import SessionDep
from app.models.usuario import Papel, Sessao, Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)
BearerDep = Annotated[str | None, Depends(oauth2_scheme)]


def current_session(
    request: Request, session: SessionDep, token: BearerDep
) -> tuple[Usuario, Sessao]:
    identity = getattr(request.state, "identity", None)
    if identity is None:
        raise unauthorized()
    return identity


def current_user(
    identity: Annotated[tuple[Usuario, Sessao], Depends(current_session)],
) -> Usuario:
    return identity[0]


def agenda_user(request: Request, session: SessionDep, token: BearerDep) -> Usuario:
    identity = getattr(request.state, "identity", None)
    if identity is None:
        raise unauthorized()
    user, _ = identity
    require_role(user, Papel.PROFISSIONAL, Papel.RECEPCIONISTA)
    return user


def require_role(user: Usuario, *roles: Papel) -> None:
    if user.papel not in roles:
        raise HTTPException(403, "Papel sem permissao para esta operacao.")


UserDep = Annotated[Usuario, Depends(current_user)]


def professional_user(user: UserDep) -> Usuario:
    require_role(user, Papel.PROFISSIONAL)
    if user.profissional_id is None:
        raise HTTPException(403, "Conta sem vinculo profissional.")
    return user


def admin_user(user: UserDep) -> Usuario:
    require_role(user, Papel.ADMIN)
    return user


ProfessionalDep = Annotated[Usuario, Depends(professional_user)]
AgendaUserDep = Annotated[Usuario, Depends(agenda_user)]
