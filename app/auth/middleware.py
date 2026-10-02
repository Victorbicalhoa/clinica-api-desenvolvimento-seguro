from secrets import token_hex

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.audit import record_request
from app.auth.integracao import authenticate_machine
from app.auth.limits import consume
from app.auth.security import authenticate

PUBLIC = {
    ("GET", "/health"),
    ("GET", "/docs"),
    ("GET", "/openapi.json"),
    ("GET", "/docs/oauth2-redirect"),
    ("GET", "/redoc"),
    ("POST", "/auth/token"),
    ("POST", "/auth/mfa"),
    ("POST", "/integracoes/token"),
}


def prepare(request: Request, public: bool) -> None:
    with Session(request.app.state.engine) as session:
        if request.method == "POST" and request.url.path in {
            "/auth/token",
            "/auth/mfa",
            "/integracoes/token",
        }:
            settings = request.app.state.settings
            peer = request.client.host if request.client else "unknown"
            consume(
                session,
                "peer",
                peer,
                settings.auth_ip_limit,
                settings.auth_window_seconds,
                request.app.state.rate_clock(),
            )
            if request.url.path in {"/auth/token", "/integracoes/token"}:
                consume(
                    session,
                    "login-peer",
                    peer,
                    settings.login_ip_limit,
                    settings.auth_window_seconds,
                    request.app.state.rate_clock(),
                )
        if not public:
            headers = request.headers.getlist("Authorization")
            scheme, value = get_authorization_scheme_param(
                headers[0] if len(headers) == 1 else None
            )
            token = value if scheme.lower() == "bearer" else None
            # Credencial explicita invalida nao pode cair no fallback cookie.
            if not headers and request.method == "GET" and request.url.path == "/agenda":
                token = request.cookies.get("agenda_session")
            if (request.method, request.url.path) == ("GET", "/integracoes/disponibilidade"):
                client = authenticate_machine(token, session, request)
                request.state.machine_id = client.client_id
                session.expunge(client)
                request.state.machine_identity = client
                settings = request.app.state.settings
                consume(
                    session,
                    "api-machine",
                    client.client_id,
                    settings.api_request_limit,
                    settings.auth_window_seconds,
                    request.app.state.rate_clock(),
                )
                return
            user, record = authenticate(token, session, request)
            session.expunge_all()
            request.state.identity = (user, record)
            request.state.audit_actor = user.id
            settings = request.app.state.settings
            if (request.method, request.url.path) != ("POST", "/auth/logout"):
                consume(
                    session,
                    "api-user",
                    str(user.id),
                    settings.api_request_limit,
                    settings.auth_window_seconds,
                    request.app.state.rate_clock(),
                )


class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = token_hex(16)
        request.state.audit_route = "<unmatched>"
        request.state.audit_resource = None
        if request.url.path in {"/auth/token", "/auth/mfa", "/integracoes/token"}:
            request.state.audit_route = request.url.path
        public = (request.method, request.url.path) in PUBLIC or (
            request.method in {"GET", "HEAD"} and request.url.path.startswith("/static/")
        )
        track = not public or request.url.path in {"/auth/token", "/auth/mfa", "/integracoes/token"}
        try:
            await run_in_threadpool(prepare, request, public)
            response = await call_next(request)
        except HTTPException as exc:
            response = JSONResponse(
                {"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers
            )
        except SQLAlchemyError:
            response = JSONResponse(
                {"detail": "Servico temporariamente indisponivel."}, status_code=503
            )
        except Exception:
            # Nao devolver nem persistir texto de excecao que pode conter dados/segredos.
            response = JSONResponse({"detail": "Erro interno."}, status_code=500)
        if track:
            if not getattr(request.state, "audit_written", False):
                try:
                    await run_in_threadpool(record_request, request, response.status_code)
                except SQLAlchemyError:
                    # Sem evento persistido, nao liberar leitura protegida.
                    response = JSONResponse({"detail": "Auditoria indisponivel."}, status_code=503)
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        response.headers["X-Request-ID"] = request.state.request_id
        return response
