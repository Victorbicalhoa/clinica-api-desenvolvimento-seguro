import jwt
import pytest
from conftest import login_as
from sqlmodel import Session, select

from app.models.seguranca import EventoAuditoria
from app.models.usuario import VinculoPaciente


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_th02_vinculo_revogado_invalida_acesso_com_jwt_ainda_valido(
    raw_client, consulta_payload, method
):
    headers = login_as(raw_client)
    created = raw_client.post("/consultas", headers=headers, json=consulta_payload)
    assert created.status_code == 201
    path = f"/consultas/{created.json()['id']}"
    with Session(raw_client.app.state.engine) as session:
        link = session.get(VinculoPaciente, (1, 1))
        session.delete(link)
        session.commit()
    kwargs = {"json": consulta_payload} if method == "put" else {}
    assert raw_client.request(method, path, headers=headers, **kwargs).status_code == 404
    assert raw_client.get("/consultas", headers=headers).json() == []


@pytest.mark.parametrize("username", ["prof1", "recepcao"])
@pytest.mark.parametrize("path", ["/admin/painel", "/admin/auditoria"])
def test_th13_papel_injetado_em_claim_e_header_nao_eleva_privilegio(raw_client, username, path):
    auth = login_as(raw_client, username)
    token = auth["Authorization"].split()[1]
    claims = jwt.decode(token, options={"verify_signature": False})
    claims["role"] = "administrador"
    claims["papel"] = "administrador"
    # Assinatura valida de teste: ainda assim, papel vem do banco, nao do claim inventado.
    modified = jwt.encode(claims, raw_client.app.state.jwt_secret, algorithm="HS256")
    response = raw_client.get(
        path, headers={"Authorization": f"Bearer {modified}", "X-Role": "administrador"}
    )
    assert response.status_code == 403


def test_th02_th05_delete_alheio_preserva_dado_e_registra_ator(raw_client, consulta_payload):
    owner = login_as(raw_client)
    other = login_as(raw_client, "prof2")
    created = raw_client.post("/consultas", headers=owner, json=consulta_payload)
    assert created.status_code == 201
    identifier = created.json()["id"]
    path = f"/consultas/{identifier}"
    denied = raw_client.delete(path, headers={**other, "X-Request-ID": "forjado"})
    assert denied.status_code == 404
    assert denied.headers["x-request-id"] != "forjado"
    assert raw_client.get(path, headers=owner).json() == created.json()
    with Session(raw_client.app.state.engine) as session:
        event = session.exec(
            select(EventoAuditoria).where(
                EventoAuditoria.request_id == denied.headers["x-request-id"]
            )
        ).one()
        assert event.ator_id == 2
        assert event.recurso_id == identifier
        assert event.status_http == 404


def test_th03_th06_put_nao_aceita_metadados_nem_altera_recurso(raw_client, consulta_payload):
    auth = login_as(raw_client)
    created = raw_client.post("/consultas", headers=auth, json=consulta_payload)
    assert created.status_code == 201
    path = f"/consultas/{created.json()['id']}"
    denied = raw_client.put(
        path,
        headers=auth,
        json={
            **consulta_payload,
            "criado_em": "2000-01-01T00:00:00Z",
            "referencia_interna": "forjada",
            "id": 999,
        },
    )
    assert denied.status_code == 422
    retrieved = raw_client.get(path, headers=auth)
    assert retrieved.json() == created.json()
    assert not {"criado_em", "referencia_interna"} & retrieved.json().keys()
