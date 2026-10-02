import asyncio
import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest
from fastapi import HTTPException, Request
from sqlalchemy.dialects import sqlite
from sqlmodel import Session
from starlette.datastructures import FormData, QueryParams

from app.auth.dependencies import require_role
from app.auth.policies import authorize_write, owned_consulta
from app.auth.validation import login_form
from app.core.network import RequestBodyLimit
from app.models.consulta import ConsultaWrite
from app.models.usuario import Papel, Usuario, VinculoPaciente
from scripts.audit_openapi import audit


def request_mock(pairs, content_type="application/x-www-form-urlencoded"):
    request = MagicMock(spec=Request)
    request.headers = {"content-type": content_type}
    request.query_params = QueryParams()
    request.form = AsyncMock(return_value=FormData(pairs))
    return request


@pytest.mark.parametrize(
    "extra",
    [
        [("username", "duplicado")],
        [("papel", "administrador")],
        [("scope", "admin")],
    ],
)
def test_mock_entrada_rejeita_duplicatas_extras_e_scope(extra):
    request = request_mock(
        [("grant_type", "password"), ("username", "prof1"), ("password", "senha-ficticia"), *extra]
    )
    with pytest.raises(HTTPException) as error:
        asyncio.run(login_form(request))
    assert error.value.status_code == 422
    request.form.assert_awaited_once()


def test_mock_entrada_tipo_invalido_nao_chama_parser():
    request = request_mock([], "multipart/form-data")
    with pytest.raises(HTTPException) as error:
        asyncio.run(login_form(request))
    assert error.value.status_code == 415
    request.form.assert_not_awaited()


def test_mock_entrada_valida_preserva_contrato():
    request = request_mock(
        [("grant_type", "password"), ("username", "prof1"), ("password", "senha-ficticia")]
    )
    result = asyncio.run(login_form(request))
    assert result.username == "prof1"
    assert result.password.get_secret_value() == "senha-ficticia"


@pytest.mark.parametrize("professional,linked", [(4, True), (2, False)])
def test_mock_autorizacao_rejeita_profissional_ou_paciente_alheio(
    consulta_payload, professional, linked
):
    session = create_autospec(Session, instance=True)
    session.get.return_value = object() if linked else None
    user = Usuario(
        id=7, username="unit", password_hash="ficticio", papel=Papel.PROFISSIONAL, profissional_id=2
    )
    data = ConsultaWrite.model_validate({**consulta_payload, "profissional_id": professional})
    with pytest.raises(HTTPException) as error:
        authorize_write(data, user, session)
    assert error.value.status_code == 403
    if professional != 2:
        session.get.assert_not_called()
    else:
        session.get.assert_called_once_with(VinculoPaciente, (7, data.paciente_id))
    session.commit.assert_not_called()


def test_mock_ownership_consulta_parametrizada_e_404():
    session = create_autospec(Session, instance=True)
    session.exec.return_value.first.return_value = None
    user = Usuario(
        id=7, username="unit", password_hash="ficticio", papel=Papel.PROFISSIONAL, profissional_id=2
    )
    with pytest.raises(HTTPException) as error:
        owned_consulta(123, session, user)
    assert error.value.status_code == 404
    statement = session.exec.call_args.args[0]
    compiled = statement.compile(dialect=sqlite.dialect())
    assert set(compiled.params.values()) == {123, 7, 2}
    assert "vinculopaciente.usuario_id = ?" in str(compiled)
    assert "consulta.profissional_id = ?" in str(compiled)
    session.commit.assert_not_called()


def test_mock_papel_nao_admin_bloqueado_sem_persistencia():
    user = MagicMock(spec=Usuario)
    user.papel = Papel.RECEPCIONISTA
    with pytest.raises(HTTPException) as error:
        require_role(user, Papel.ADMIN)
    assert error.value.status_code == 403


@pytest.mark.parametrize("declared", [None, b"1", b"999999"])
def test_mock_limite_conta_bytes_reais_sem_confiar_content_length(declared):
    downstream = AsyncMock()
    receive = AsyncMock(
        side_effect=[
            {"type": "http.request", "body": b"12345", "more_body": True},
            {"type": "http.request", "body": b"67890", "more_body": False},
        ]
    )
    send = AsyncMock()
    scope = {
        "type": "http",
        "method": "POST",
        "headers": [] if declared is None else [(b"content-length", declared)],
    }
    asyncio.run(RequestBodyLimit(downstream, 9)(scope, receive, send))
    downstream.assert_not_awaited()
    assert send.await_args_list[0].args[0]["status"] == 413


def test_body_limit_413_preserva_headers_cors(raw_client):
    raw_client.app.state.settings.max_request_body_bytes = 65_536
    response = raw_client.post(
        "/auth/token", content=b"x" * 65_537, headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 413
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'none'" in response.headers["content-security-policy"]


def test_openapi_capstone_contrato_seguro(raw_client):
    result = audit(raw_client.get("/openapi.json").json())
    assert result["passed"], [x for x in result["checks"] if not x["passed"]]


def test_docs_locais_csp_e_integridade_de_assets(raw_client):
    from app.core.config import PROJECT_ROOT

    response = raw_client.get("/docs")
    assert response.status_code == 200
    assert "unsafe-inline" not in response.headers["content-security-policy"]
    assert "unsafe-eval" not in response.headers["content-security-policy"]
    assert "cdn.jsdelivr.net" not in response.text
    assert "<script>" not in response.text
    assert "/static/docs-init.js" in response.text
    manifest = json.loads((PROJECT_ROOT / "security/vendor-assets.json").read_text())
    for entry in manifest["files"]:
        assert (
            hashlib.sha256((PROJECT_ROOT / entry["path"]).read_bytes()).hexdigest()
            == entry["sha256"]
        )
        if entry["path"].endswith((".js", ".css")):
            assert entry["sri"] in response.text
            assert raw_client.get("/" + entry["path"].removeprefix("app/")).status_code == 200
    redirected = raw_client.get("/redoc", follow_redirects=False)
    assert redirected.status_code == 307
    assert redirected.headers["location"].endswith("/docs")
