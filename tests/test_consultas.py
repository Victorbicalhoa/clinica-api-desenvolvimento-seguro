import pytest
from fastapi.testclient import TestClient


def test_criar_e_buscar_consulta(client: TestClient, consulta_payload: dict) -> None:
    response = client.post("/consultas", json=consulta_payload)
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int) and body["id"] > 0
    assert body == {
        "id": body["id"],
        "paciente_id": 1,
        "profissional_id": 2,
        "data_hora": "2030-10-15T12:00:00Z",
        "status": "agendada",
        "observacao": "",
    }
    assert response.headers["location"] == f"/consultas/{body['id']}"
    fetched = client.get(response.headers["location"])
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_listar_com_paginacao(client: TestClient, consulta_payload: dict) -> None:
    assert client.get("/consultas").json() == []
    first = client.post("/consultas", json=consulta_payload).json()
    second = client.post(
        "/consultas",
        json={**consulta_payload, "paciente_id": 3, "data_hora": "2030-10-15T10:00:00-03:00"},
    ).json()
    response = client.get("/consultas?offset=1&limit=1")
    assert response.status_code == 200
    assert response.json() == [second]
    assert client.get("/consultas?limit=1").json() == [first]


def test_atualizar_e_excluir_consulta(client: TestClient, consulta_payload: dict) -> None:
    created = client.post("/consultas", json=consulta_payload).json()
    path = f"/consultas/{created['id']}"
    updated_payload = {
        **consulta_payload,
        "profissional_id": 2,
        "data_hora": "2030-10-16T10:00:00-03:00",
        "status": "cancelada",
    }
    response = client.put(path, json=updated_payload)
    assert response.status_code == 200
    assert response.json() == {
        **updated_payload,
        "observacao": "",
        "id": created["id"],
        "data_hora": "2030-10-16T13:00:00Z",
    }
    assert client.get(path).json() == response.json()
    deleted = client.delete(path)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(path).status_code == 404
    assert client.get("/consultas").json() == []


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_consulta_inexistente(client: TestClient, consulta_payload: dict, method: str) -> None:
    kwargs = {"json": consulta_payload} if method == "put" else {}
    response = client.request(method, "/consultas/999", **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": "Consulta nao encontrada."}


@pytest.mark.parametrize(
    "change",
    [
        {"paciente_id": 0},
        {"paciente_id": True},
        {"paciente_id": "1"},
        {"profissional_id": -1},
        {"status": "inexistente"},
        {"data_hora": "2030-10-15T09:00:00"},
        {"data_hora": "data-invalida"},
        {"data_hora": "0001-01-01T00:00:00+03:00"},
        {"data_hora": "9999-12-31T23:59:59-03:00"},
        {"data_hora": 123},
        {"campo_extra": "nao permitido"},
        {"id": 999},
    ],
)
def test_criacao_invalida_nao_persiste(
    client: TestClient, consulta_payload: dict, change: dict
) -> None:
    response = client.post("/consultas", json={**consulta_payload, **change})
    assert response.status_code == 422
    assert client.get("/consultas").json() == []


def test_put_incompleto_nao_altera_registro(client: TestClient, consulta_payload: dict) -> None:
    created = client.post("/consultas", json=consulta_payload).json()
    path = f"/consultas/{created['id']}"
    response = client.put(path, json={"status": "cancelada"})
    assert response.status_code == 422
    assert client.get(path).json() == created


@pytest.mark.parametrize(
    "query", ["limit=0", "limit=101", "offset=-1", "offset=9223372036854775808"]
)
def test_paginacao_invalida(client: TestClient, query: str) -> None:
    assert client.get(f"/consultas?{query}").status_code == 422
