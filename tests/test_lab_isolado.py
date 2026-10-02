"""LABORATORIO RECONSTRUIDO VULNERAVEL, somente teste em memoria.

Nunca importar de app/ nem executar com uvicorn. Nao e baseline historica de producao.
O mesmo recurso persistido, identidade e payload passam pela versao fraca e pela real.
"""

from html.parser import HTMLParser

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from jinja2 import Environment
from markupsafe import escape
from sqlmodel import select

from app.auth.dependencies import UserDep
from app.auth.middleware import JWTMiddleware
from app.database.session import SessionDep
from app.models.consulta import Consulta, ConsultaRead
from tests.conftest import login_as


class ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.scripts += 1


def vulnerable_lab(real_client):
    lab = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    # Apenas memoria/banco descartavel fornecido pela fixture, sem app global exportavel.
    for name, value in real_client.app.state._state.items():
        setattr(lab.state, name, value)
    lab.add_middleware(JWTMiddleware)

    @lab.get("/consultas/{consulta_id}", response_model=ConsultaRead)
    def missing_ownership(consulta_id: int, user: UserDep, session: SessionDep):
        # FALHA DIDATICA: usuario autenticado, mas sem predicado de ownership.
        record = session.get(Consulta, consulta_id)
        if record is None:
            raise HTTPException(404)
        return record

    @lab.get("/agenda", response_class=HTMLResponse)
    def missing_escape(user: UserDep, session: SessionDep):
        rows = session.exec(
            select(Consulta).where(Consulta.profissional_id == user.profissional_id)
        ).all()
        # FALHA DIDATICA: conteudo persistido vira markup executavel no HTML.
        template = Environment(autoescape=False).from_string(
            "<table>{% for item in rows %}<tr><td>{{ item.observacao }}</td></tr>"
            "{% endfor %}</table>"
        )
        return template.render(rows=rows)

    return lab


def compare_before_after(raw_client):
    alice, bob = login_as(raw_client, "prof1"), login_as(raw_client, "prof2")
    other = raw_client.post(
        "/consultas",
        headers=bob,
        json={
            "paciente_id": 100,
            "profissional_id": 4,
            "data_hora": "2030-10-15T12:00:00Z",
            "observacao": "PRONTUARIO FICTICIO DE OUTRO VINCULO",
        },
    )
    assert other.status_code == 201
    identifier = other.json()["id"]
    payload = '<script>alert("XSS-LAB")</script>'
    stored = raw_client.post(
        "/consultas",
        headers=alice,
        json={
            "paciente_id": 1,
            "profissional_id": 2,
            "data_hora": "2030-10-15T12:00:00Z",
            "observacao": payload,
        },
    )
    assert stored.status_code == 201
    with TestClient(vulnerable_lab(raw_client)) as before:
        leak = before.get(f"/consultas/{identifier}", headers=alice)
        vulnerable_html = before.get("/agenda?dia=2030-10-15", headers=alice)
    protected = raw_client.get(f"/consultas/{identifier}", headers=alice)
    safe_html = raw_client.get("/agenda?dia=2030-10-15", headers=alice)
    unsafe_dom, safe_dom = ScriptParser(), ScriptParser()
    unsafe_dom.feed(vulnerable_html.text)
    safe_dom.feed(safe_html.text)
    assert leak.status_code == 200 and leak.json()["paciente_id"] == 100
    assert protected.status_code == 404
    assert vulnerable_html.status_code == safe_html.status_code == 200
    assert unsafe_dom.scripts == 1 and safe_dom.scripts == 0
    assert payload in vulnerable_html.text and str(escape(payload)) in safe_html.text
    return {
        "kind": "reconstructed-test-laboratory; not historical production",
        "same_identity_and_payload": True,
        "bola": {
            "request": f"GET /consultas/{identifier}",
            "actor": "prof1",
            "before_status": 200,
            "after_status": 404,
            "before_exposed_other_patient": True,
            "fix": "app/auth/policies.py: owned_consulta/scope_consultas",
        },
        "stored_xss": {
            "payload": payload,
            "persisted_through_real_api": True,
            "before_script_elements": 1,
            "after_script_elements": 0,
            "escaped_after": True,
            "fix": "app/core/templates.py + app/templates/agenda.html",
        },
        "limits": (
            "HTTP/HTML parser; no browser Javascript execution claimed. "
            "No vulnerable route in production."
        ),
    }


def test_lab_bola_xss_mesmo_ataque_antes_depois(raw_client):
    compare_before_after(raw_client)
