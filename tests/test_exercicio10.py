import pytest
from conftest import login_as
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app

ORIGIN = "http://localhost:3000"


def assert_headers(response, https=False):
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    if https:
        assert response.headers["strict-transport-security"] == "max-age=31536000"
    else:
        assert "strict-transport-security" not in response.headers


@pytest.mark.parametrize("origin", ["http://localhost:3000", "http://127.0.0.1:3000"])
def test_cors_preflight_allowlist_sem_autenticacao(raw_client, origin):
    response = raw_client.options(
        "/consultas",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "Origin" in response.headers["vary"]
    assert "*" not in response.headers["access-control-allow-methods"]
    assert "access-control-allow-credentials" not in response.headers
    assert_headers(response)
    # Preflight autorizado nao autoriza o recurso.
    denied = raw_client.get("/consultas", headers={"Origin": origin})
    assert denied.status_code == 401
    assert denied.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize(
    "origin",
    ["https://evil.example", "null", "http://localhost:3001", "http://localhost:3000.evil.example"],
)
def test_cors_origem_nao_autorizada(raw_client, origin):
    preflight = raw_client.options(
        "/consultas", headers={"Origin": origin, "Access-Control-Request-Method": "GET"}
    )
    assert preflight.status_code == 400
    assert "access-control-allow-origin" not in preflight.headers
    assert_headers(preflight)
    simple = raw_client.get("/health", headers={"Origin": origin})
    assert simple.status_code == 200  # CORS controla leitura no browser, nao firewall.
    assert "access-control-allow-origin" not in simple.headers


@pytest.mark.parametrize(
    "extra",
    [
        {"Access-Control-Request-Method": "PATCH"},
        {"Access-Control-Request-Headers": "X-Override-Role"},
    ],
)
def test_cors_metodo_e_header_fora_da_allowlist(raw_client, extra):
    response = raw_client.options(
        "/consultas", headers={"Origin": ORIGIN, "Access-Control-Request-Method": "GET", **extra}
    )
    assert response.status_code == 400
    assert_headers(response)


@pytest.mark.parametrize(
    "bad",
    [
        "*",
        "https://*.clinica.example",
        "null",
        "http://clinica.example",
        "https://user:pass@clinica.example",
        "https://clinica.example/path",
        "https://clinica.example?x=1",
        "https://clinica.example#x",
        " https://clinica.example",
    ],
)
def test_config_rejeita_cors_inseguro(bad):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_allow_origins=[bad])


def test_config_normaliza_origem_explicita():
    settings = Settings(
        _env_file=None, cors_allow_origins=["https://clinica.example/", "https://clinica.example"]
    )
    assert settings.cors_allow_origins == ["https://clinica.example"]


def test_headers_http_https_e_forwarded_nao_confiavel(raw_client):
    http = raw_client.get("/health", headers={"X-Forwarded-Proto": "https"})
    assert_headers(http)
    https = raw_client.get("https://testserver/health")
    assert https.status_code == 200
    assert_headers(https, https=True)
    preflight = raw_client.options(
        "https://testserver/consultas",
        headers={"Origin": ORIGIN, "Access-Control-Request-Method": "GET"},
    )
    assert preflight.status_code == 200
    assert_headers(preflight, https=True)


def test_headers_cors_em_403_422_429(raw_client, consulta_payload):
    headers = {**login_as(raw_client), "Origin": ORIGIN}
    denied = raw_client.get("/admin/painel", headers=headers)
    invalid = raw_client.post(
        "/consultas", headers=headers, json={**consulta_payload, "extra": "x"}
    )
    raw_client.app.state.settings.api_request_limit = 1
    limited = raw_client.get("/consultas", headers=headers)
    assert [r.status_code for r in (denied, invalid, limited)] == [403, 422, 429]
    for response in (denied, invalid, limited):
        assert response.headers["access-control-allow-origin"] == ORIGIN
        assert_headers(response)
    assert "Retry-After" in limited.headers["access-control-expose-headers"]
    assert int(limited.headers["retry-after"]) > 0


def test_camadas_externas_cobrem_500_fora_do_jwt(raw_client):
    app = create_app(engine=raw_client.app.state.engine, settings=Settings(_env_file=None))

    @app.middleware("http")
    async def failure(request, call_next):
        raise RuntimeError("falha fora do middleware JWT")

    with TestClient(app, base_url="https://testserver", raise_server_exceptions=False) as client:
        response = client.get("/health", headers={"Origin": ORIGIN})
    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert_headers(response, https=True)


def test_login_diferenciado_nao_bloqueia_leitura_e_logout(raw_client):
    headers = login_as(raw_client)
    wrong = {"grant_type": "password", "username": "alvo", "password": "invalida"}
    for _ in range(5):
        assert raw_client.post("/auth/token", data=wrong).status_code == 401
    assert raw_client.post("/auth/token", data=wrong).status_code == 429
    # A quota do login nao consome a quota de recursos.
    assert raw_client.get("/consultas", headers=headers).status_code == 200
    raw_client.app.state.settings.api_request_limit = 1
    assert raw_client.get("/consultas", headers=headers).status_code == 429
    assert raw_client.post("/auth/logout", headers=headers).status_code == 204
    assert raw_client.get("/consultas", headers=headers).status_code == 401


def test_login_por_ip_limita_troca_de_username(raw_client):
    raw_client.app.state.settings.login_ip_limit = 2
    for name in ("a", "b"):
        response = raw_client.post(
            "/auth/token", data={"grant_type": "password", "username": name, "password": "invalida"}
        )
        assert response.status_code == 401
    third = raw_client.post(
        "/auth/token",
        data={"grant_type": "password", "username": "c", "password": "invalida"},
        headers={"X-Forwarded-For": "203.0.113.4"},
    )
    assert third.status_code == 429
    raw_client.app.state.rate_clock = lambda: 6060.0
    assert (
        raw_client.post(
            "/auth/token", data={"grant_type": "password", "username": "c", "password": "invalida"}
        ).status_code
        == 401
    )


def test_nova_sessao_nao_reinicia_quota_do_usuario(raw_client):
    raw_client.app.state.settings.api_request_limit = 1
    first = login_as(raw_client)
    assert raw_client.get("/consultas", headers=first).status_code == 200
    second = login_as(raw_client)
    assert first != second
    assert raw_client.get("/consultas", headers=second).status_code == 429
    raw_client.app.state.rate_clock = lambda: 6060.0
    assert raw_client.get("/consultas", headers=second).status_code == 200
