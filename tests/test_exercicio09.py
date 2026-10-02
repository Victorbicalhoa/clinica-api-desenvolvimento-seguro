from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from conftest import TEST_PASSWORD, login_as
from fastapi.testclient import TestClient
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, create_engine, select

from app.auth import consultas_service
from app.core.config import Settings
from app.main import create_app
from app.models.consulta import Consulta
from app.models.seguranca import EventoAuditoria
from app.models.usuario import Papel, Usuario, VinculoPaciente


def test_middleware_fecha_rota_nova_sem_dep_e_nao_confia_em_header(raw_client):
    @raw_client.app.get("/nova-sem-dep")
    def new_endpoint():
        return {"ok": True}

    assert raw_client.get("/nova-sem-dep", headers={"X-User-ID": "1"}).status_code == 401
    assert raw_client.get("/nova-sem-dep", headers=login_as(raw_client)).status_code == 200
    assert raw_client.get("/auth/token/extra").status_code == 401
    assert raw_client.get("/docs/extra").status_code == 401
    assert raw_client.get("/health").status_code == 200


def test_jwt_e_validado_uma_vez_e_cookie_nao_salva_bearer_invalido(raw_client, monkeypatch):
    from app.auth import middleware

    real = middleware.authenticate
    calls = []

    def counted(*args):
        calls.append(True)
        return real(*args)

    monkeypatch.setattr(middleware, "authenticate", counted)
    headers = login_as(raw_client)
    assert raw_client.get("/consultas", headers=headers).status_code == 200
    assert len(calls) == 1
    assert raw_client.post("/auth/browser-session", headers=headers).status_code == 204
    assert (
        raw_client.get("/agenda", headers={"Authorization": "Bearer invalido"}).status_code == 401
    )


def test_erro_inesperado_tem_evento_sem_segredo(raw_client):
    @raw_client.app.get("/falha-simulada")
    def broken():
        raise RuntimeError("SEGREDO-QUE-NAO-PODE-SAIR")

    response = raw_client.get("/falha-simulada", headers=login_as(raw_client))
    assert response.status_code == 500
    assert response.headers["cache-control"] == "no-store"
    assert "SEGREDO-QUE" not in response.text
    with Session(raw_client.app.state.engine) as session:
        records = session.exec(
            select(EventoAuditoria).where(
                EventoAuditoria.request_id == response.headers["x-request-id"]
            )
        ).all()
        assert len(records) == 1 and records[0].status_http == 500
        assert "SEGREDO-QUE" not in str(records)


def test_leitura_e_negacao_preservam_id_alvo_sem_query(raw_client, consulta_payload):
    owner = login_as(raw_client)
    other = login_as(raw_client, "prof2")
    response = raw_client.post("/consultas", headers=owner, json=consulta_payload)
    resource = response.json()["id"]
    for headers, expected in [(owner, 200), (other, 404)]:
        read = raw_client.get(f"/consultas/{resource}?segredo=NAO-LOGAR", headers=headers)
        assert read.status_code == expected
        with Session(raw_client.app.state.engine) as session:
            record = session.exec(
                select(EventoAuditoria).where(
                    EventoAuditoria.request_id == read.headers["x-request-id"]
                )
            ).one()
            assert record.recurso_id == resource and record.rota == "/consultas/{consulta_id}"
            assert record.status_http == expected and "NAO-LOGAR" not in str(record)


@pytest.mark.parametrize(
    "extra",
    [
        {"papel": "administrador"},
        {"username": "a' OR 1=1 --"},
        {"scope": "admin"},
        {"grant_type": "client_credentials"},
    ],
)
def test_login_whitelist_regex_sem_refletir_segredos(raw_client, extra):
    data = {"grant_type": "password", "username": "prof1", "password": TEST_PASSWORD, **extra}
    response = raw_client.post("/auth/token", data=data)
    assert response.status_code == 422
    assert TEST_PASSWORD not in response.text


@pytest.mark.parametrize("endpoint", ["/auth/browser-session", "/auth/logout"])
def test_endpoints_adicionais_rejeitam_campos_sem_efeito(raw_client, endpoint):
    headers = login_as(raw_client)
    assert raw_client.post(endpoint, headers=headers, json={"usuario_id": 2}).status_code == 422
    assert raw_client.get("/consultas", headers=headers).status_code == 200
    assert raw_client.post(endpoint, headers=headers).status_code == 204


def test_erros_pydantic_nao_refletem_input(client, consulta_payload):
    response = client.post("/consultas", json={**consulta_payload, "observacao": "SIGILO" * 100})
    assert response.status_code == 422
    assert "SIGILO" not in response.text and '"input"' not in response.text
    with Session(client.app.state.engine) as session:
        stored = session.exec(select(EventoAuditoria)).all()
        assert "SIGILO" not in str(stored)


def test_budget_por_conta_e_ip_recupera_sem_confiar_forwarded(raw_client):
    raw_client.app.state.rate_clock = lambda: 6000.0
    raw_client.app.state.settings.auth_login_limit = 2
    bad = {"grant_type": "password", "username": "prof1", "password": "errada"}
    assert raw_client.post("/auth/token", data=bad).status_code == 401
    assert raw_client.post("/auth/token", data=bad).status_code == 401
    blocked = raw_client.post("/auth/token", data=bad, headers={"X-Forwarded-For": "1.2.3.4"})
    assert blocked.status_code == 429 and blocked.headers["retry-after"] == "60"
    raw_client.app.state.rate_clock = lambda: 6060.0
    assert (
        raw_client.post("/auth/token", data={**bad, "password": TEST_PASSWORD}).status_code == 200
    )
    raw_client.app.state.settings.auth_ip_limit = 1
    assert raw_client.post("/auth/token", data={**bad, "username": "outro"}).status_code == 429


def test_budget_mfa_nao_reseta_com_novo_desafio(raw_client):
    raw_client.app.state.settings.auth_mfa_limit = 2

    def start():
        response = raw_client.post(
            "/auth/token",
            data={"grant_type": "password", "username": "admin", "password": TEST_PASSWORD},
        )
        assert response.status_code == 202
        return response.json()["challenge_id"]

    first = start()
    code = raw_client.app.state.test_codes[first]
    wrong = "000000" if code != "000000" else "000001"
    for _ in range(2):
        assert (
            raw_client.post("/auth/mfa", json={"challenge_id": first, "code": wrong}).status_code
            == 401
        )
    second = start()
    correct = raw_client.app.state.test_codes[second]
    assert (
        raw_client.post("/auth/mfa", json={"challenge_id": second, "code": correct}).status_code
        == 429
    )


def test_budget_compartilhado_entre_instancias(raw_client):
    raw_client.app.state.settings.auth_login_limit = 2
    raw_client.app.state.rate_clock = lambda: 6000.0
    other_app = create_app(
        engine=raw_client.app.state.engine, settings=Settings(_env_file=None, auth_login_limit=2)
    )
    with TestClient(other_app) as other:
        other.app.state.rate_clock = lambda: 6000.0
        data = {"grant_type": "password", "username": "prof1", "password": "invalida"}
        assert raw_client.post("/auth/token", data=data).status_code == 401
        assert other.post("/auth/token", data=data).status_code == 401
        assert raw_client.post("/auth/token", data=data).status_code == 429


def test_dialeto_nao_suportado_rejeitado_antes_de_ddl(monkeypatch):
    from types import SimpleNamespace

    from sqlmodel import SQLModel

    from app.database.session import create_tables

    calls = []
    monkeypatch.setattr(SQLModel.metadata, "create_all", lambda *args: calls.append(True))
    with pytest.raises(RuntimeError):
        create_tables(SimpleNamespace(dialect=SimpleNamespace(name="postgresql")))
    assert calls == []


def test_auditoria_papeis_eventos_redacao_e_append_only(raw_client, consulta_payload):
    owner = login_as(raw_client)
    admin = login_as(raw_client, "admin")
    secret = "DADO-CLINICO-NAO-LOGAR"
    created = raw_client.post(
        "/consultas", json={**consulta_payload, "observacao": secret}, headers=owner
    )
    assert created.status_code == 201
    record_id = created.json()["id"]
    assert raw_client.get("/admin/auditoria", headers=owner).status_code == 403
    events = raw_client.get("/admin/auditoria?limit=100", headers=admin)
    assert events.status_code == 200
    assert (
        secret not in events.text
        and TEST_PASSWORD not in events.text
        and "access_token" not in events.text
    )
    assert any(
        x["acao"] == "consulta.criar" and x["ator_id"] == 1 and x["recurso_id"] == record_id
        for x in events.json()
    )
    assert raw_client.get("/admin/auditoria?campo=extra", headers=admin).status_code == 422
    with Session(raw_client.app.state.engine) as session:
        for statement in (delete(EventoAuditoria), update(EventoAuditoria).values(status_http=200)):
            with pytest.raises(IntegrityError):
                session.exec(statement)
                session.commit()
            session.rollback()


def test_falha_de_auditoria_reverte_mutacao(client, consulta_payload, monkeypatch):
    def fail(*args):
        raise SQLAlchemyError("Falha simulada no destino de auditoria")

    monkeypatch.setattr(consultas_service, "mutation", fail)
    response = client.post("/consultas", json=consulta_payload)
    assert response.status_code == 503
    with Session(client.app.state.engine) as session:
        assert session.exec(select(Consulta)).all() == []


def test_conflito_cancelamento_transicoes_e_put(client, consulta_payload):
    first = client.post("/consultas", json=consulta_payload)
    assert first.status_code == 201
    path = f"/consultas/{first.json()['id']}"
    assert client.post("/consultas", json=consulta_payload).status_code == 409
    other_payload = {**consulta_payload, "data_hora": "2030-10-15T13:00:00Z"}
    second = client.post("/consultas", json=other_payload)
    assert second.status_code == 201
    second_path = f"/consultas/{second.json()['id']}"
    assert client.put(second_path, json=consulta_payload).status_code == 409
    assert client.put(path, json={**consulta_payload, "status": "cancelada"}).status_code == 200
    assert client.post("/consultas", json=consulta_payload).status_code == 201
    assert client.put(path, json=consulta_payload).status_code == 409
    assert client.put(second_path, json={**other_payload, "status": "realizada"}).status_code == 200
    assert client.put(second_path, json=other_payload).status_code == 409


def test_conflito_concorrente_persistido_em_conexoes_distintas(password_hash, consulta_payload):
    root = Path(__file__).resolve().parents[1] / ".cache" / f"slot-test-{uuid4().hex}"
    root.mkdir(parents=True)
    database = root / "test.db"
    engine = create_engine(
        f"sqlite:///{database.as_posix()}", connect_args={"check_same_thread": False, "timeout": 10}
    )
    try:
        with TestClient(create_app(engine=engine, settings=Settings(_env_file=None))) as client:
            with Session(engine) as session:
                session.add(
                    Usuario(
                        id=1,
                        username="prof1",
                        password_hash=password_hash,
                        papel=Papel.PROFISSIONAL,
                        profissional_id=2,
                    )
                )
                session.flush()
                session.add(VinculoPaciente(usuario_id=1, paciente_id=1))
                session.commit()
            headers = login_as(client)
            barrier = Barrier(2)

            def send():
                barrier.wait(timeout=10)
                return client.post("/consultas", json=consulta_payload, headers=headers).status_code

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(send) for _ in range(2)]
                statuses = sorted(future.result(timeout=20) for future in futures)
            assert statuses == [201, 409]
            with Session(engine) as session:
                assert len(session.exec(select(Consulta)).all()) == 1
                assert (
                    len(
                        session.exec(
                            select(EventoAuditoria).where(EventoAuditoria.acao == "consulta.criar")
                        ).all()
                    )
                    == 1
                )
    finally:
        engine.dispose()
        for suffix in ("", "-wal", "-shm", "-journal"):
            database.with_name(database.name + suffix).unlink(missing_ok=True)
        root.rmdir()
