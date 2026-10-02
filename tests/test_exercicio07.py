from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlmodel import Session, select

from app.auth.integracao import MACHINE_AUDIENCE
from app.auth.security import ALGORITHM, ISSUER, hash_password
from app.models.consulta import Consulta, StatusConsulta
from app.models.integracao import (
    SCOPE_AVAILABILITY,
    ClienteIntegracao,
    ClienteProfissional,
    EventoIntegracao,
    SlotOferta,
)
from app.models.usuario import Usuario
from tests.conftest import login_as

SECRET = "Segredo-Ficticio-Laboratorio-Teste-2026!"
DAY = "2030-10-15"


@pytest.fixture(scope="session")
def machine_hash():
    return hash_password(SECRET)


@pytest.fixture
def machine_client(raw_client, machine_hash):
    with Session(raw_client.app.state.engine) as session:
        session.add(ClienteIntegracao(client_id="lab", secret_hash=machine_hash))
        session.flush()
        session.add(ClienteProfissional(client_id="lab", profissional_id=2))
        for pid, hour in [(2, 12), (2, 13), (2, 14), (4, 12)]:
            session.add(
                SlotOferta(profissional_id=pid, inicio=datetime(2030, 10, 15, hour, tzinfo=UTC))
            )
        for hour, status in [(12, StatusConsulta.AGENDADA), (13, StatusConsulta.CANCELADA)]:
            session.add(
                Consulta(
                    paciente_id=1,
                    profissional_id=2,
                    data_hora=datetime(2030, 10, 15, hour, tzinfo=UTC),
                    status=status,
                    observacao="DADO CLINICO FICTICIO PRIVADO",
                )
            )
        session.commit()
    return raw_client


def token(client, **form):
    return client.post(
        "/integracoes/token",
        auth=("lab", SECRET),
        data={"grant_type": "client_credentials", **form},
    )


def bearer(client):
    response = token(client)
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_m2m_disponibilidade_minima_scopes_claims_auditoria(machine_client):
    response = token(machine_client)
    assert response.status_code == 200
    assert set(response.json()) == {"access_token", "token_type", "expires_in", "scope"}
    assert response.json()["scope"] == SCOPE_AVAILABILITY
    assert response.json()["expires_in"] == 300
    assert response.headers["cache-control"] == "no-store"
    claims = jwt.decode(
        response.json()["access_token"],
        machine_client.app.state.jwt_secret,
        algorithms=[ALGORITHM],
        audience=MACHINE_AUDIENCE,
        issuer=ISSUER,
    )
    assert claims["token_use"] == "machine" and claims["sub"] == claims["client_id"] == "lab"
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    available = machine_client.get(
        "/integracoes/disponibilidade", params={"dia": DAY}, headers=headers
    )
    assert available.status_code == 200
    assert [row["inicio"][11:13] for row in available.json()] == ["13", "14"]
    assert all(
        set(row) == {"profissional_id", "inicio"} and row["profissional_id"] == 2
        for row in available.json()
    )
    assert "PRIVADO" not in available.text
    with Session(machine_client.app.state.engine) as session:
        events = session.exec(select(EventoIntegracao)).all()
        assert len(events) == 2
        assert all(e.client_id == "lab" and e.status_http == 200 for e in events)


@pytest.mark.parametrize(
    "form",
    [
        {"scope": ""},
        {"scope": "admin"},
        {"scope": "disponibilidade:read consultas:read"},
        {"grant_type": "password"},
        {"papel": "administrador"},
        {"client_secret": SECRET},
    ],
)
def test_m2m_formulario_fechado(machine_client, form):
    assert token(machine_client, **form).status_code == 400


@pytest.mark.parametrize("auth", [("lab", "incorreto"), ("ausente", SECRET), None])
def test_m2m_credenciais_genericas(machine_client, auth):
    response = machine_client.post(
        "/integracoes/token", auth=auth, data={"grant_type": "client_credentials"}
    )
    # Ausencia de header viola contrato de request; IDs/segredos errados sao indistintos.
    assert response.status_code == (400 if auth is None else 401)
    assert SECRET not in response.text


@pytest.mark.parametrize("path", ["/consultas", "/admin/painel", "/agenda"])
def test_m2m_nao_acessa_rotas_humanas(machine_client, path):
    assert machine_client.get(path, headers=bearer(machine_client)).status_code == 401


def test_humano_nao_acessa_m2m(machine_client):
    headers = login_as(machine_client)
    assert (
        machine_client.get("/integracoes/disponibilidade?dia=" + DAY, headers=headers).status_code
        == 401
    )


@pytest.mark.parametrize(
    "mutation", ["exp", "aud", "token_use", "client_id", "scope", "version", "missing"]
)
def test_m2m_claims_adulteradas_negadas(machine_client, mutation):
    headers = bearer(machine_client)
    claims = jwt.decode(
        headers["Authorization"].split()[1],
        machine_client.app.state.jwt_secret,
        algorithms=[ALGORITHM],
        audience=MACHINE_AUDIENCE,
    )
    changes = {
        "exp": int((datetime.now(UTC) - timedelta(seconds=1)).timestamp()),
        "aud": "clinica-humanos",
        "token_use": "human",
        "client_id": "outro",
        "scope": "",
        "version": True,
    }
    if mutation == "missing":
        del claims["scope"]
    else:
        claims[mutation] = changes[mutation]
    bad = jwt.encode(claims, machine_client.app.state.jwt_secret, algorithm=ALGORITHM)
    response = machine_client.get(
        "/integracoes/disponibilidade?dia=" + DAY, headers={"Authorization": "Bearer " + bad}
    )
    assert response.status_code == (403 if mutation == "scope" else 401)


@pytest.mark.parametrize("change", ["disabled", "version", "scope", "link", "professional"])
def test_m2m_revogacao_revalida_banco(machine_client, change):
    headers = bearer(machine_client)
    with Session(machine_client.app.state.engine) as session:
        record = session.get(ClienteIntegracao, "lab")
        if change == "disabled":
            record.ativo = False
        elif change == "version":
            record.token_version += 1
        elif change == "scope":
            record.scopes = ""
        elif change == "link":
            session.delete(session.get(ClienteProfissional, ("lab", 2)))
        else:
            user = session.get(Usuario, 1)
            user.ativo = False
            session.add(user)
        session.add(record)
        session.commit()
    response = machine_client.get("/integracoes/disponibilidade?dia=" + DAY, headers=headers)
    if change in {"link", "professional"}:
        assert response.status_code == 200 and response.json() == []
    else:
        assert response.status_code == (403 if change == "scope" else 401)


def test_m2m_limita_tentativas_antes_bcrypt(machine_client, monkeypatch):
    from app.routes import integracoes

    for _ in range(5):
        assert (
            machine_client.post(
                "/integracoes/token",
                auth=("lab", "errado"),
                data={"grant_type": "client_credentials"},
            ).status_code
            == 401
        )

    def forbidden(*args):
        pytest.fail("bcrypt nao deve executar apos esgotamento da quota")

    monkeypatch.setattr(integracoes, "verify_password", forbidden)
    response = token(machine_client)
    assert response.status_code == 429 and "retry-after" in response.headers


def test_m2m_headers_e_campos_duplicados(machine_client):
    response = machine_client.post(
        "/integracoes/token",
        auth=("lab", SECRET),
        content="grant_type=client_credentials&scope=disponibilidade%3Aread&scope=admin",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 400
    headers = bearer(machine_client)
    response = machine_client.get(
        "/integracoes/disponibilidade?dia=" + DAY,
        headers=[
            ("Authorization", headers["Authorization"]),
            ("Authorization", headers["Authorization"]),
        ],
    )
    assert response.status_code == 401


@pytest.mark.parametrize(
    "query",
    [
        "dia=9999-12-31",
        "dia=2030-10-15&limit=101",
        "dia=2030-10-15&papel=admin",
        "dia=2030-10-15&dia=2030-10-16",
    ],
)
def test_m2m_query_limitada(machine_client, query):
    assert (
        machine_client.get(
            "/integracoes/disponibilidade?" + query, headers=bearer(machine_client)
        ).status_code
        == 422
    )


def test_m2m_quota_nao_enumera_cliente(machine_client):
    sequences = []
    for identifier in ("lab", "cliente_inexistente"):
        sequences.append(
            [
                machine_client.post(
                    "/integracoes/token",
                    auth=(identifier, "errado"),
                    data={"grant_type": "client_credentials"},
                ).status_code
                for _ in range(6)
            ]
        )
    assert sequences == [[401, 401, 401, 401, 401, 429]] * 2


def test_m2m_cliente_desativado_nao_obtem_token(machine_client):
    with Session(machine_client.app.state.engine) as session:
        client = session.get(ClienteIntegracao, "lab")
        client.ativo = False
        session.add(client)
        session.commit()
    assert token(machine_client).status_code == 401
