"""Identidade de maquinas separada de identidade/papeis humanos."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi import HTTPException, Request
from sqlmodel import Session

from app.auth.security import ALGORITHM, ISSUER, unauthorized
from app.models.integracao import SCOPE_AVAILABILITY, ClienteIntegracao, MachineTokenRead

MACHINE_AUDIENCE = "clinica-laboratorio"


def issue_machine_token(client: ClienteIntegracao, scope: str, request: Request):
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": client.client_id,
            "client_id": client.client_id,
            "token_use": "machine",
            "aud": MACHINE_AUDIENCE,
            "iss": ISSUER,
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(seconds=300),
            "jti": str(uuid4()),
            "scope": scope,
            "version": client.token_version,
        },
        request.app.state.jwt_secret,
        algorithm=ALGORITHM,
    )
    return MachineTokenRead(access_token=token, scope=scope)


def authenticate_machine(token: str | None, session: Session, request: Request):
    if not token:
        raise unauthorized()
    try:
        claims = jwt.decode(
            token,
            request.app.state.jwt_secret,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=MACHINE_AUDIENCE,
            options={
                "require": [
                    "sub",
                    "client_id",
                    "token_use",
                    "aud",
                    "iss",
                    "iat",
                    "nbf",
                    "exp",
                    "jti",
                    "scope",
                    "version",
                ]
            },
        )
        if (
            claims["token_use"] != "machine"
            or claims["aud"] != MACHINE_AUDIENCE
            or not isinstance(claims["sub"], str)
            or claims["client_id"] != claims["sub"]
            or type(claims["version"]) is not int
            or not isinstance(claims["jti"], str)
            or not isinstance(claims["scope"], str)
        ):
            raise ValueError("Claims invalidas")
        client = session.get(ClienteIntegracao, claims["sub"])
        if client is None or not client.ativo or client.token_version != claims["version"]:
            raise ValueError("Cliente inativo")
    except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError) as exc:
        raise unauthorized() from exc
    scopes = set(claims["scope"].split())
    if scopes != {SCOPE_AVAILABILITY} or not scopes <= set(client.scopes.split()):
        raise HTTPException(
            403,
            "Escopo insuficiente.",
            headers={
                "WWW-Authenticate": (
                    'Bearer error="insufficient_scope", scope="disponibilidade:read"'
                )
            },
        )
    return client
