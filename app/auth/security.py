from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

import bcrypt
import jwt
from fastapi import HTTPException, Request
from sqlmodel import Session

from app.models.usuario import Papel, Sessao, TokenRead, Usuario

ALGORITHM = "HS256"
ISSUER = "clinica-assessment"
AUDIENCE = "clinica-humanos"


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(password) < 12 or len(raw) > 72:
        raise ValueError("Senha deve ter ao menos 12 caracteres e no maximo 72 bytes UTF-8.")
    return bcrypt.hashpw(raw, bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    raw = password.encode("utf-8")
    if len(raw) > 72:
        return False
    try:
        return bcrypt.checkpw(raw, hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


def unauthorized() -> HTTPException:
    return HTTPException(
        401,
        "Credenciais invalidas ou sessao expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def issue_token(
    user: Usuario, session: Session, request: Request, *, mfa: bool = False
) -> TokenRead:
    now = datetime.now(UTC)
    ttl = request.app.state.settings.access_token_minutes * 60
    expiration = now + timedelta(seconds=ttl)
    jti = str(uuid4())
    session.add(Sessao(jti=jti, usuario_id=user.id, expira_em=expiration, mfa=mfa))
    session.commit()
    token = jwt.encode(
        {
            "sub": str(user.id),
            "jti": jti,
            "iat": now,
            "nbf": now,
            "exp": expiration,
            "iss": ISSUER,
            "aud": AUDIENCE,
            "mfa": mfa,
            "token_use": "human",
        },
        request.app.state.jwt_secret,
        algorithm=ALGORITHM,
    )
    return TokenRead(access_token=token, expires_in=ttl)


def authenticate(token: str | None, session: Session, request: Request) -> tuple[Usuario, Sessao]:
    if not token:
        raise unauthorized()
    try:
        claims = jwt.decode(
            token,
            request.app.state.jwt_secret,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require": ["sub", "jti", "iat", "nbf", "exp", "iss", "aud", "mfa", "token_use"]
            },
        )
        subject = claims["sub"]
        if claims["token_use"] != "human":
            raise ValueError("Invalid token use")
        if (
            not isinstance(subject, str)
            or not subject.isascii()
            or not subject.isdecimal()
            or len(subject) > 10
        ):
            raise ValueError("Invalid subject")
        if not isinstance(claims["jti"], str) or type(claims["mfa"]) is not bool:
            raise ValueError("Invalid claims")
        record = session.get(Sessao, claims["jti"])
        user = session.get(Usuario, int(subject))
        if (
            record is None
            or user is None
            or not user.ativo
            or record.revogada
            or record.usuario_id != user.id
            or record.expira_em <= datetime.now(UTC)
            or record.mfa != claims["mfa"]
            or (user.papel == Papel.ADMIN and not record.mfa)
        ):
            raise ValueError("Inactive session")
        return user, record
    except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError) as exc:
        raise unauthorized() from exc


def ephemeral_key() -> str:
    return token_urlsafe(48)
