from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.auth.security import hash_password
from app.core.config import Settings
from app.main import create_app
from app.models.usuario import Papel, Usuario, VinculoPaciente

TEST_PASSWORD = "Senha-Ficticia-Teste-2026!"


@pytest.fixture(scope="session")
def password_hash():
    return hash_password(TEST_PASSWORD)


@pytest.fixture
def raw_client(password_hash) -> Generator[TestClient, None, None]:
    # Banco novo por teste; nunca abre data/clinica.db.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        codes = {}
        settings = Settings(_env_file=None, mfa_simulated=True, cookie_secure=False)
        with TestClient(
            create_app(
                engine=engine,
                settings=settings,
                mfa_sender=lambda challenge, code: codes.__setitem__(challenge, code),
            )
        ) as test_client:
            test_client.app.state.test_codes = codes
            test_client.app.state.rate_clock = lambda: 6000.0
            with Session(engine) as session:
                for uid, name, role, professional in [
                    (1, "prof1", Papel.PROFISSIONAL, 2),
                    (2, "prof2", Papel.PROFISSIONAL, 4),
                    (3, "recepcao", Papel.RECEPCIONISTA, None),
                    (4, "admin", Papel.ADMIN, None),
                ]:
                    session.add(
                        Usuario(
                            id=uid,
                            username=name,
                            password_hash=password_hash,
                            papel=role,
                            profissional_id=professional,
                        )
                    )
                session.flush()
                for patient in range(1, 52):
                    session.add(VinculoPaciente(usuario_id=1, paciente_id=patient))
                session.add(VinculoPaciente(usuario_id=2, paciente_id=100))
                session.commit()
            yield test_client
    finally:
        engine.dispose()


def login_as(client, username="prof1"):
    response = client.post(
        "/auth/token",
        data={
            "grant_type": "password",
            "username": username,
            "password": TEST_PASSWORD,
        },
    )
    if response.status_code == 202:
        challenge = response.json()["challenge_id"]
        response = client.post(
            "/auth/mfa",
            json={
                "challenge_id": challenge,
                "code": client.app.state.test_codes[challenge],
            },
        )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def client(raw_client):
    # Regressao antiga agora passa pela autenticacao real, sem override de seguranca.
    raw_client.headers.update(login_as(raw_client))
    return raw_client


@pytest.fixture
def consulta_payload() -> dict:
    return {
        "paciente_id": 1,
        "profissional_id": 2,
        "data_hora": "2030-10-15T09:00:00-03:00",
        "status": "agendada",
    }
