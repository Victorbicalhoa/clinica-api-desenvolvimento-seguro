from contextlib import asynccontextmanager
from time import time

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Engine

from app.auth.middleware import JWTMiddleware
from app.auth.security import ephemeral_key, hash_password
from app.core.config import PROJECT_ROOT, Settings, get_settings
from app.core.network import HardenedAPI
from app.core.openapi import configure_openapi
from app.database.session import build_engine, create_tables
from app.routes.admin import router as admin_router
from app.routes.agenda import router as agenda_router
from app.routes.auth import router as auth_router
from app.routes.consultas import router as consultas_router
from app.routes.docs import router as docs_router
from app.routes.health import router as health_router
from app.routes.integracoes import router as integracoes_router


def create_app(
    engine: Engine | None = None, settings: Settings | None = None, mfa_sender=None
) -> FastAPI:
    resolved_settings = settings if settings is not None else get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = resolved_settings
        database_engine = engine if engine is not None else build_engine(app.state.settings)
        app.state.engine = database_engine
        configured_key = app.state.settings.jwt_secret
        app.state.jwt_secret = (
            configured_key.get_secret_value() if configured_key else ephemeral_key()
        )
        app.state.dummy_hash = hash_password(ephemeral_key())
        app.state.mfa_sender = mfa_sender or simulated_mfa_sender
        app.state.rate_clock = time
        try:
            create_tables(database_engine)
            yield
        finally:
            if engine is None:
                database_engine.dispose()

    app = HardenedAPI(
        network_settings=resolved_settings,
        title="API de Agendamento de Consultas",
        version="0.1.0",
        description="Assessment: use somente dados ficticios neste ambiente local.",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        swagger_ui_oauth2_redirect_url=None,
    )
    app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "app" / "static"), name="static")
    app.include_router(agenda_router)
    app.include_router(health_router)
    app.include_router(consultas_router)
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(docs_router)
    app.include_router(integracoes_router)
    configure_openapi(app)
    app.add_middleware(JWTMiddleware)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Pydantic inclui input por padrao: nao devolver senhas, OTP ou observacao.
        errors = [
            {"type": item["type"], "loc": item["loc"], "msg": "Entrada invalida."}
            for item in exc.errors()
        ]
        return JSONResponse({"detail": errors}, status_code=422)

    @app.middleware("http")
    async def prevent_sensitive_cache(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith(("/auth/", "/admin/", "/consultas", "/agenda")):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        return response

    return app


def simulated_mfa_sender(challenge: str, code: str) -> None:
    # Somente demonstracao local explicitamente habilitada; nao e segundo canal real.
    print(f"[MFA SIMULADO LOCAL] desafio={challenge} codigo={code}", flush=True)


app = create_app()
