import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from conftest import login_as
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import URL
from sqlmodel import Session, select

from app.core.config import PROJECT_ROOT, Settings
from app.database.session import build_engine, get_session
from app.main import create_app
from app.models.usuario import Papel, Usuario, VinculoPaciente


@pytest.fixture(autouse=True)
def isolated_settings_environment(monkeypatch):
    # _env_file escolhe o arquivo, mas nao desativa precedencia do ambiente.
    for name in list(os.environ):
        if name.lower() in Settings.model_fields:
            monkeypatch.delenv(name)


@pytest.fixture
def disk_directory():
    directory = (Path(".cache") / ("persistence-" + uuid4().hex)).resolve()
    directory.mkdir(parents=True)
    try:
        yield directory.resolve()
    finally:
        # Somente arquivos conhecidos, em diretorio exclusivo deste teste.
        for name in ["test.db", "test.db-journal", "test.db-wal", "test.db-shm", ".env"]:
            (directory / name).unlink(missing_ok=True)
        directory.rmdir()


def test_persistencia_duas_instancias_e_token_antigo(
    disk_directory, password_hash, consulta_payload
):
    url = URL.create("sqlite", database=str(disk_directory / "test.db"))
    env_file = disk_directory / ".env"
    env_file.write_text("DATABASE_URL=" + url.render_as_string() + "\n", encoding="utf-8")
    settings = Settings(_env_file=env_file)
    with TestClient(create_app(settings=settings)) as client:
        assert Path(client.app.state.engine.url.database) == disk_directory / "test.db"
        with Session(client.app.state.engine) as session:
            user = Usuario(
                username="prof1",
                password_hash=password_hash,
                papel=Papel.PROFISSIONAL,
                profissional_id=2,
            )
            session.add(user)
            session.flush()
            session.add(VinculoPaciente(usuario_id=user.id, paciente_id=1))
            session.commit()
        auth = login_as(client)
        created = client.post("/consultas", json=consulta_payload, headers=auth)
        assert created.status_code == 201
        consultation_id = created.json()["id"]
    assert (disk_directory / "test.db").stat().st_size > 0
    with TestClient(create_app(settings=Settings(_env_file=env_file))) as restarted:
        assert Path(restarted.app.state.engine.url.database) == disk_directory / "test.db"
        assert restarted.get(f"/consultas/{consultation_id}", headers=auth).status_code == 401
        new_auth = login_as(restarted)
        response = restarted.get(f"/consultas/{consultation_id}", headers=new_auth)
        assert response.status_code == 200
        assert response.json()["paciente_id"] == 1


def test_env_precedencia_e_url_nao_exposta(disk_directory, monkeypatch):
    env_file = disk_directory / ".env"
    env_file.write_text("DATABASE_URL=sqlite:///from-file.db\n", encoding="utf-8")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from_file = Settings(_env_file=env_file)
    assert from_file.database_url.get_secret_value() == "sqlite:///from-file.db"
    assert "from-file.db" not in repr(from_file)
    assert "from-file.db" not in from_file.model_dump_json()
    monkeypatch.setenv("DATABASE_URL", "sqlite:///from-environment.db")
    assert (
        Settings(_env_file=env_file).database_url.get_secret_value().endswith("from-environment.db")
    )


@pytest.mark.parametrize("url", ["sqlite://", "sqlite:///:memory:"])
def test_memoria_apenas_quando_configurada_explicitamente(url):
    engine = build_engine(Settings(_env_file=None, database_url=url))
    try:
        assert str(engine.url) == url
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://user:SENTINELA_FICTICIA@host/db",
        "sqlite+aiosqlite:///test.db",
        "invalida-SENTINELA_FICTICIA",
        "sqlite:///file:test.db?uri=true",
        "sqlite:///file:test.db",
        "sqlite:///test.db?mode=memory",
    ],
)
def test_url_nao_suportada_falha_sem_expor_valor(url):
    settings = Settings(_env_file=None, database_url=url)
    with pytest.raises(ValueError) as error:
        build_engine(settings)
    assert str(error.value) == "DATABASE_URL deve indicar SQLite local sem credenciais ou query."
    assert "SENTINELA_FICTICIA" not in repr(settings)


def test_caminho_relativo_estavel_e_parametros_ocultos(disk_directory, monkeypatch):
    with monkeypatch.context() as scoped:
        scoped.chdir(disk_directory)
        engine = build_engine(Settings(_env_file=None, database_url="sqlite:///./data/test.db"))
    try:
        assert Path(engine.url.database) == (PROJECT_ROOT / "data/test.db").resolve()
        assert engine.hide_parameters is True
        assert engine.echo is False
    finally:
        engine.dispose()


def test_payload_sql_separado_do_comando_no_driver(raw_client, consulta_payload):
    payload = "x'); DROP TABLE consulta; --"
    captured = []

    def observe(conn, cursor, statement, parameters, context, executemany):
        captured.append((statement, parameters))

    auth = login_as(raw_client)
    event.listen(raw_client.app.state.engine, "before_cursor_execute", observe)
    try:
        response = raw_client.post(
            "/consultas", headers=auth, json={**consulta_payload, "observacao": payload}
        )
        assert response.status_code == 201
        path = "/consultas/" + str(response.json()["id"])
        updated = raw_client.put(
            path, headers=auth, json={**consulta_payload, "observacao": payload + "update"}
        )
        assert updated.status_code == 200
        assert raw_client.get(path, headers=auth).json()["observacao"] == payload + "update"
        # SELECT com valor atacante tambem permanece parametrizado, sem ampliar resultados.
        with Session(raw_client.app.state.engine) as session:
            assert session.exec(select(Usuario).where(Usuario.username == payload)).all() == []
        for operation in ("INSERT INTO consulta", "UPDATE consulta", "SELECT usuario"):
            relevant = [
                (sql, params)
                for sql, params in captured
                if sql.startswith(operation) and payload in str(params)
            ]
            assert relevant, operation
            assert all(payload not in sql and "?" in sql for sql, _ in relevant)
    finally:
        event.remove(raw_client.app.state.engine, "before_cursor_execute", observe)


def test_dependencia_rollback_e_fechamento(raw_client, monkeypatch):
    import app.database.session as database

    closed = []

    class TrackedSession(Session):
        def close(self):
            closed.append(True)
            super().close()

    monkeypatch.setattr(database, "Session", TrackedSession)
    dependency = get_session(SimpleNamespace(app=raw_client.app))
    session = next(dependency)
    session.add(
        Usuario(username="rollback", password_hash="ficticio-sem-login", papel=Papel.RECEPCIONISTA)
    )
    session.flush()
    with pytest.raises(RuntimeError, match="falha simulada"):
        dependency.throw(RuntimeError("falha simulada"))
    assert closed == [True]
    with Session(raw_client.app.state.engine) as verify:
        assert verify.exec(select(Usuario).where(Usuario.username == "rollback")).first() is None
