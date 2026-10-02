from datetime import UTC, datetime, timedelta

import jwt
import pytest
from conftest import TEST_PASSWORD, login_as
from sqlmodel import Session, select

from app.auth.security import (
    ALGORITHM,
    AUDIENCE,
    ISSUER,
    hash_password,
    verify_password,
)
from app.models.usuario import DesafioMFA, Papel, Sessao, Usuario, VinculoPaciente


def test_nao_administrador_impedido_de_acessar_rota_admin(raw_client):
    headers = login_as(raw_client)
    response = raw_client.get("/admin/painel", headers=headers)
    assert response.status_code == 403
    assert "mfa_verified" not in response.text
    assert raw_client.get("/admin/painel", headers=login_as(raw_client, "admin")).status_code == 200


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/consultas"),
        ("post", "/consultas"),
        ("get", "/consultas/1"),
        ("put", "/consultas/1"),
        ("delete", "/consultas/1"),
        ("get", "/agenda"),
        ("get", "/admin/painel"),
    ],
)
def test_sem_token_bloqueado(raw_client, consulta_payload, method, path):
    response = raw_client.request(
        method, path, json=consulta_payload if method in ("post", "put") else None
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_ownership_crud_listas_agenda_e_vinculos(raw_client, consulta_payload):
    owner = login_as(raw_client)
    other = login_as(raw_client, "prof2")
    created = raw_client.post(
        "/consultas",
        headers=owner,
        json={**consulta_payload, "observacao": "SOMENTE-DONO"},
    )
    assert created.status_code == 201
    path = f"/consultas/{created.json()['id']}"
    for method in ("get", "put", "delete"):
        kwargs = {"json": consulta_payload} if method == "put" else {}
        assert raw_client.request(method, path, headers=other, **kwargs).status_code == 404
    assert raw_client.get("/consultas", headers=other).json() == []
    assert "SOMENTE-DONO" not in raw_client.get("/agenda?dia=2030-10-15", headers=other).text
    assert raw_client.post("/consultas", headers=other, json=consulta_payload).status_code == 403
    assert (
        raw_client.post(
            "/consultas", headers=owner, json={**consulta_payload, "paciente_id": 100}
        ).status_code
        == 403
    )
    assert (
        raw_client.put(
            path, headers=owner, json={**consulta_payload, "profissional_id": 4}
        ).status_code
        == 403
    )
    assert (
        raw_client.put(
            path, headers=owner, json={**consulta_payload, "paciente_id": 100}
        ).status_code
        == 403
    )
    assert raw_client.get(path, headers=owner).json() == created.json()
    own_other = {**consulta_payload, "profissional_id": 4, "paciente_id": 100}
    assert raw_client.post("/consultas", headers=other, json=own_other).status_code == 201
    with Session(raw_client.app.state.engine) as session:
        link = session.get(VinculoPaciente, (1, 1))
        session.delete(link)
        session.commit()
    assert raw_client.get(path, headers=owner).status_code == 404
    assert raw_client.get("/consultas", headers=owner).json() == []


@pytest.mark.parametrize("username", ["recepcao", "admin"])
def test_papeis_sem_poder_clinico(raw_client, consulta_payload, username):
    headers = login_as(raw_client, username)
    for method, path in [
        ("post", "/consultas"),
        ("get", "/consultas"),
        ("get", "/consultas/1"),
        ("put", "/consultas/1"),
        ("delete", "/consultas/1"),
    ]:
        response = raw_client.request(
            method,
            path,
            headers=headers,
            json=consulta_payload if method in ("post", "put") else None,
        )
        assert response.status_code == 403


def test_recepcao_agenda_minima_e_cookie_so_leitura(raw_client, consulta_payload):
    owner = login_as(raw_client)
    raw_client.post(
        "/consultas",
        headers=owner,
        json={**consulta_payload, "observacao": "SEGREDO-CLINICO"},
    )
    reception = login_as(raw_client, "recepcao")
    assert raw_client.post("/auth/browser-session", headers=reception).status_code == 204
    agenda = raw_client.get("/agenda?dia=2030-10-15")
    assert agenda.status_code == 200
    assert len(agenda.context["consultas"]) == 1
    assert agenda.context["consultas"][0].observacao == ""
    assert "SEGREDO-CLINICO" not in agenda.text
    assert raw_client.post("/consultas", json=consulta_payload).status_code == 401
    assert raw_client.post("/auth/browser-session").status_code == 401
    cookie = raw_client.post("/auth/browser-session", headers=reception).headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie and "Path=/agenda" in cookie


def test_mfa_somente_apos_senha_sem_token_antes_e_sem_replay(raw_client):
    start = raw_client.post(
        "/auth/token",
        data={"grant_type": "password", "username": "admin", "password": TEST_PASSWORD},
    )
    assert start.status_code == 202
    body = start.json()
    assert set(body) == {"challenge_id", "mfa_required", "expires_in"}
    challenge = body["challenge_id"]
    code = raw_client.app.state.test_codes[challenge]
    wrong = "000000" if code != "000000" else "000001"
    assert (
        raw_client.post("/auth/mfa", json={"challenge_id": challenge, "code": wrong}).status_code
        == 401
    )
    success = raw_client.post("/auth/mfa", json={"challenge_id": challenge, "code": code})
    assert success.status_code == 200
    assert (
        raw_client.post("/auth/mfa", json={"challenge_id": challenge, "code": code}).status_code
        == 401
    )
    token = success.json()["access_token"]
    assert (
        raw_client.get("/admin/painel", headers={"Authorization": f"Bearer {token}"}).status_code
        == 200
    )


@pytest.mark.parametrize("mode", ["expired", "attempts", "disabled"])
def test_mfa_expiracao_limite_desativacao(raw_client, mode):
    start = raw_client.post(
        "/auth/token",
        data={"grant_type": "password", "username": "admin", "password": TEST_PASSWORD},
    )
    challenge = start.json()["challenge_id"]
    code = raw_client.app.state.test_codes[challenge]
    if mode == "expired":
        with Session(raw_client.app.state.engine) as session:
            item = session.get(DesafioMFA, challenge)
            item.expira_em = datetime.now(UTC) - timedelta(seconds=1)
            session.add(item)
            session.commit()
    elif mode == "attempts":
        wrong = "000000" if code != "000000" else "000001"
        for _ in range(5):
            assert (
                raw_client.post(
                    "/auth/mfa", json={"challenge_id": challenge, "code": wrong}
                ).status_code
                == 401
            )
    else:
        raw_client.app.state.settings.mfa_simulated = False
    assert raw_client.post(
        "/auth/mfa", json={"challenge_id": challenge, "code": code}
    ).status_code == (429 if mode == "attempts" else 401)


@pytest.mark.parametrize(
    "mutation",
    [
        "expired",
        "issuer",
        "audience",
        "signature",
        "algorithm",
        "missing",
        "subject",
        "mfa",
    ],
)
def test_jwt_invalido_negado(raw_client, mutation):
    token = login_as(raw_client)["Authorization"].split()[1]
    secret = raw_client.app.state.jwt_secret
    claims = jwt.decode(token, secret, algorithms=[ALGORITHM], audience=AUDIENCE, issuer=ISSUER)
    algorithm = ALGORITHM
    if mutation == "expired":
        claims["exp"] = int((datetime.now(UTC) - timedelta(seconds=1)).timestamp())
    elif mutation == "issuer":
        claims["iss"] = "outro"
    elif mutation == "audience":
        claims["aud"] = "laboratorio"
    elif mutation == "signature":
        secret = "invalida" * 8
    elif mutation == "algorithm":
        algorithm = "HS384"
    elif mutation == "missing":
        del claims["exp"]
    elif mutation == "subject":
        claims["sub"] = "9" * 100
    else:
        claims["mfa"] = True
    invalid = jwt.encode(claims, secret, algorithm=algorithm)
    assert (
        raw_client.get("/consultas", headers={"Authorization": f"Bearer {invalid}"}).status_code
        == 401
    )


def test_logout_desativacao_e_papel_atual(raw_client):
    headers = login_as(raw_client)
    assert raw_client.get("/consultas", headers=headers).status_code == 200
    assert raw_client.post("/auth/logout", headers=headers).status_code == 204
    assert raw_client.get("/consultas", headers=headers).status_code == 401
    headers = login_as(raw_client)
    with Session(raw_client.app.state.engine) as session:
        user = session.get(Usuario, 1)
        user.ativo = False
        session.add(user)
        session.commit()
    assert raw_client.get("/consultas", headers=headers).status_code == 401
    with Session(raw_client.app.state.engine) as session:
        user = session.get(Usuario, 1)
        user.ativo = True
        user.papel = Papel.ADMIN
        session.add(user)
        session.commit()
    # Promover no banco nao transforma token sem MFA em sessao administrativa.
    assert raw_client.get("/admin/painel", headers=headers).status_code == 401


def test_senhas_hash_e_login_generico(raw_client, password_hash):
    assert password_hash.startswith("$2b$12$") and TEST_PASSWORD not in password_hash
    assert verify_password(TEST_PASSWORD, password_hash)
    assert not verify_password("errada", password_hash)
    with pytest.raises(ValueError):
        hash_password("a" * 73)
    with pytest.raises(ValueError):
        hash_password("á" * 37)
    wrong = raw_client.post(
        "/auth/token",
        data={"grant_type": "password", "username": "prof1", "password": "errada"},
    )
    absent = raw_client.post(
        "/auth/token",
        data={"grant_type": "password", "username": "naoexiste", "password": "errada"},
    )
    assert wrong.status_code == absent.status_code == 401
    assert wrong.json() == absent.json()
    with Session(raw_client.app.state.engine) as session:
        assert all(
            TEST_PASSWORD not in item.password_hash for item in session.exec(select(Usuario)).all()
        )
        assert session.exec(select(Sessao)).all() == []


def test_factory_respeita_database_url_injetada():
    from fastapi.testclient import TestClient

    from app.core.config import Settings
    from app.main import create_app

    settings = Settings(_env_file=None, database_url="sqlite://")
    with TestClient(create_app(settings=settings)) as client:
        assert str(client.app.state.engine.url) == "sqlite://"
        assert client.app.state.settings is settings
        assert client.get("/health").status_code == 200


def test_provisionamento_duplicado_sem_traceback_ou_hash(raw_client, monkeypatch, capsys):
    from app.auth import provision

    monkeypatch.setattr(provision, "build_engine", lambda: raw_client.app.state.engine)
    monkeypatch.setattr(provision, "getpass", lambda prompt: TEST_PASSWORD)
    monkeypatch.setattr(
        "sys.argv", ["provision", "duplicado", "--papel", "profissional", "--profissional-id", "2"]
    )
    with pytest.raises(SystemExit) as result:
        provision.main()
    assert result.value.code == 2
    error = capsys.readouterr().err
    assert "Usuario ou profissional ja vinculado" in error
    assert "$2b$" not in error and TEST_PASSWORD not in error and "Traceback" not in error


def test_cookie_secure_por_padrao_e_respostas_sem_cache(raw_client):
    raw_client.app.state.settings.cookie_secure = True
    headers = login_as(raw_client)
    response = raw_client.post("/auth/browser-session", headers=headers)
    assert "Secure" in response.headers["set-cookie"]
    for path in ("/consultas", "/agenda", "/admin/painel"):
        response = raw_client.get(path, headers=headers)
        assert response.headers["cache-control"] == "no-store"


def test_mfa_desativado_nao_libera_administrador(raw_client):
    raw_client.app.state.settings.mfa_simulated = False
    response = raw_client.post(
        "/auth/token",
        data={"grant_type": "password", "username": "admin", "password": TEST_PASSWORD},
    )
    assert response.status_code == 503
    assert "access_token" not in response.json()
    assert raw_client.app.state.test_codes == {}


def test_openapi_exige_oauth2_nas_rotas_protegidas(raw_client):
    paths = raw_client.get("/openapi.json").json()["paths"]
    for path, methods in paths.items():
        if path.startswith(("/consultas", "/agenda", "/admin")):
            for operation in methods.values():
                assert {"OAuth2PasswordBearer": []} in operation["security"]
