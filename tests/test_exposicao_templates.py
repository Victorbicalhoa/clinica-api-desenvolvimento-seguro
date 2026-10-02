from datetime import UTC, date, datetime, timedelta
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape
from sqlmodel import Session

from app.core.templates import environment
from app.models.consulta import Consulta, ConsultaRead
from app.routes.agenda import hoje_utc

PUBLIC_FIELDS = {
    "id",
    "paciente_id",
    "profissional_id",
    "data_hora",
    "status",
    "observacao",
}
INTERNAL_FIELDS = {"criado_em", "referencia_interna"}


def test_auditoria_persistida_mas_ausente_em_todas_respostas(
    client: TestClient, consulta_payload: dict
) -> None:
    created = client.post("/consultas", json=consulta_payload)
    assert created.status_code == 201
    record_id = created.json()["id"]
    with Session(client.app.state.engine) as session:
        record = session.get(Consulta, record_id)
        assert record.criado_em.tzinfo is not None
        assert record.referencia_interna
        record.referencia_interna = "AUDITORIA-NAO-EXIBIR"
        session.add(record)
        session.commit()
    responses = [
        created.json(),
        client.get(f"/consultas/{record_id}").json(),
        client.get("/consultas").json()[0],
        client.put(f"/consultas/{record_id}", json=consulta_payload).json(),
    ]
    for body in responses:
        assert set(body) == PUBLIC_FIELDS
        assert INTERNAL_FIELDS.isdisjoint(body)
        assert "AUDITORIA-NAO-EXIBIR" not in str(body)
    html = client.get("/agenda?dia=2030-10-15")
    assert html.status_code == 200
    assert html.headers["cache-control"] == "no-store"
    assert html.headers["content-type"].startswith("text/html")
    assert "AUDITORIA-NAO-EXIBIR" not in html.text
    for field in INTERNAL_FIELDS:
        assert field not in html.text
    # Verifica o contexto real do TemplateResponse, nao apenas o HTML final.
    assert len(html.context["consultas"]) == 1
    assert isinstance(html.context["consultas"][0], ConsultaRead)
    assert set(html.context["consultas"][0].model_dump()) == PUBLIC_FIELDS


@pytest.mark.parametrize("field", sorted(INTERNAL_FIELDS))
@pytest.mark.parametrize("method", ["post", "put"])
def test_cliente_nao_pode_definir_auditoria(
    client: TestClient, consulta_payload: dict, field: str, method: str
) -> None:
    created = client.post("/consultas", json=consulta_payload).json()
    path = "/consultas" if method == "post" else f"/consultas/{created['id']}"
    response = client.request(method, path, json={**consulta_payload, field: "injetado"})
    assert response.status_code == 422
    assert client.get(f"/consultas/{created['id']}").json() == created


class ParsedHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.attributes = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.extend(attrs)

    def handle_data(self, data):
        self.text.append(data)


@pytest.mark.parametrize(
    "payload",
    [
        '<script>alert("XSS")</script>',
        '<img src=x onerror="alert(1)">',
        '</td><svg onload="alert(1)"></svg><td>',
        "{{ 7 * 7 }} & <b>texto</b> \"aspas\" 'simples'",
    ],
)
def test_xss_persistido_renderizado_como_texto(
    client: TestClient, consulta_payload: dict, payload: str
) -> None:
    response = client.post("/consultas", json={**consulta_payload, "observacao": payload})
    assert response.status_code == 201
    record_id = response.json()["id"]
    with Session(client.app.state.engine) as session:
        assert session.get(Consulta, record_id).observacao == payload
    assert client.get(f"/consultas/{record_id}").json()["observacao"] == payload
    html = client.get("/agenda?dia=2030-10-15")
    assert html.status_code == 200
    assert str(escape(payload)) in html.text
    parsed = ParsedHTML()
    parsed.feed(html.text)
    assert payload in "".join(parsed.text)
    assert not {"script", "img", "svg", "b"}.intersection(parsed.tags)
    assert not any(name.lower().startswith("on") for name, value in parsed.attributes)


def test_agenda_do_dia_utc_e_heranca(client: TestClient, consulta_payload: dict) -> None:
    samples = [
        ("2030-10-14T23:59:59Z", "ONTEM"),
        ("2030-10-15T00:00:00Z", "INICIO"),
        ("2030-10-15T23:59:59Z", "FIM"),
        ("2030-10-16T00:00:00Z", "AMANHA"),
    ]
    for moment, note in samples:
        assert (
            client.post(
                "/consultas",
                json={**consulta_payload, "data_hora": moment, "observacao": note},
            ).status_code
            == 201
        )
    client.app.dependency_overrides[hoje_utc] = lambda: date(2030, 10, 15)
    try:
        response = client.get("/agenda")
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.template.name == "agenda.html"
    assert "INICIO" in response.text and "FIM" in response.text
    assert "ONTEM" not in response.text and "AMANHA" not in response.text
    assert response.text.index("INICIO") < response.text.index("FIM")
    assert "<!doctype html>" in response.text  # herdado de base.html
    assert 'lang="pt-BR"' in response.text
    assert "Agenda de consultas" in response.text
    assert "Horários em UTC" in response.text
    assert environment.autoescape("agenda.html")
    assert environment.autoescape("base.html")


def test_agenda_vazia_e_paginacao(client: TestClient) -> None:
    empty = client.get("/agenda?dia=2030-10-15")
    assert empty.status_code == 200
    assert "Nenhuma consulta nesta página" in empty.text
    with Session(client.app.state.engine) as session:
        for index in range(51):
            session.add(
                Consulta(
                    paciente_id=index + 1,
                    profissional_id=2,
                    data_hora=datetime(2030, 10, 15, 12, tzinfo=UTC) + timedelta(minutes=index),
                    observacao=f"LINHA-{index:03d}",
                )
            )
        session.commit()
    first = client.get("/agenda?dia=2030-10-15")
    second = client.get("/agenda?dia=2030-10-15&pagina=2")
    assert len(first.context["consultas"]) == 50
    assert first.context["tem_proxima"] is True
    assert "LINHA-050" not in first.text
    assert len(second.context["consultas"]) == 1
    assert second.context["tem_proxima"] is False
    assert "LINHA-050" in second.text


@pytest.mark.parametrize("query", ["dia=invalido", "dia=9999-12-31", "pagina=0"])
def test_agenda_parametros_invalidos(client: TestClient, query: str) -> None:
    assert client.get(f"/agenda?{query}").status_code == 422


def test_openapi_publica_apenas_contratos_publicos(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    read = schema["components"]["schemas"]["ConsultaRead"]["properties"]
    assert set(read) == PUBLIC_FIELDS
    assert INTERNAL_FIELDS.isdisjoint(
        schema["components"]["schemas"]["ConsultaWrite"]["properties"]
    )
    assert "Consulta" not in schema["components"]["schemas"]


def test_observacao_tem_limite(client: TestClient, consulta_payload: dict) -> None:
    assert (
        client.post("/consultas", json={**consulta_payload, "observacao": "x" * 501}).status_code
        == 422
    )
