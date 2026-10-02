from collections.abc import Generator
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import Engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import PROJECT_ROOT, Settings, get_settings


def build_engine(settings: Settings | None = None) -> Engine:
    configured = (settings if settings is not None else get_settings()).database_url
    try:
        url = make_url(configured.get_secret_value())
        if url.drivername not in {"sqlite", "sqlite+pysqlite"}:
            raise ValueError
        if url.username or url.password or url.host or url.port or url.query:
            raise ValueError
        if url.database and url.database.startswith("file:"):
            raise ValueError
    except (ArgumentError, ValueError, TypeError):
        raise ValueError(
            "DATABASE_URL deve indicar SQLite local sem credenciais ou query."
        ) from None
    # Caminhos relativos sao estaveis mesmo quando o processo parte de outro diretorio.
    # Memoria fica disponivel para engines de teste explicitamente configurados.
    if url.database and url.database != ":memory:":
        path = Path(url.database)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        url = url.set(database=str(path.resolve()))
    return create_engine(
        url, connect_args={"check_same_thread": False}, echo=False, hide_parameters=True
    )


def create_tables(engine: Engine) -> None:
    # Registrar os modelos antes de criar o esquema.
    from app.models.consulta import (
        SLOT_INDEX,
        Consulta,  # noqa: F401
    )
    from app.models.integracao import (  # noqa: F401
        ClienteIntegracao,
        ClienteProfissional,
        EventoIntegracao,
        SlotOferta,
    )
    from app.models.seguranca import EventoAuditoria, OrcamentoAuth  # noqa: F401
    from app.models.usuario import (  # noqa: F401
        DesafioMFA,
        Sessao,
        Usuario,
        VinculoPaciente,
    )

    if engine.dialect.name != "sqlite":
        raise RuntimeError("Esta versao requer SQLite para os controles transacionais.")
    SQLModel.metadata.create_all(engine)
    # Em banco existente, falha se houver duplicidades; nunca apagar dados para migrar.
    SLOT_INDEX.create(engine, checkfirst=True)
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TRIGGER IF NOT EXISTS machine_audit_no_update "
                "BEFORE UPDATE ON eventointegracao "
                "BEGIN SELECT RAISE(ABORT, 'audit_append_only'); END"
            )
        )
        connection.execute(
            text(
                "CREATE TRIGGER IF NOT EXISTS machine_audit_no_delete "
                "BEFORE DELETE ON eventointegracao "
                "BEGIN SELECT RAISE(ABORT, 'audit_append_only'); END"
            )
        )
        connection.execute(
            text(
                "CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON eventoauditoria "
                "BEGIN SELECT RAISE(ABORT, 'audit_append_only'); END"
            )
        )
        connection.execute(
            text(
                "CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON eventoauditoria "
                "BEGIN SELECT RAISE(ABORT, 'audit_append_only'); END"
            )
        )


def get_session(request: Request) -> Generator[Session, None, None]:
    with Session(request.app.state.engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
