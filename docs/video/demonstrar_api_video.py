"""Ensaio do video: cliente HTTP local, sem imprimir senha, token ou cookie.

Executar com a API de demonstracao ativa em 127.0.0.1:8000.
Contas esperadas: video_prof1 (profissional 901, paciente 9001),
video_prof2 (profissional 902, paciente 9002). Criar via provisionamento normal.
O script cria uma consulta ficticia nova em cada execucao; nunca usa dados reais.
"""

import json
from datetime import UTC, datetime, timedelta
from getpass import getpass

import httpx
from markupsafe import escape


def expect(response, status, label):
    if response.status_code != status:
        raise RuntimeError(f"{label}: HTTP {response.status_code}; esperado {status}.")
    print(f"{label}: HTTP {response.status_code}", flush=True)


def demonstrate(client, password_one, password_two, pause=input):
    headers = []
    for username, password in (
        ("video_prof1", password_one),
        ("video_prof2", password_two),
    ):
        response = client.post(
            "/auth/token",
            data={"grant_type": "password", "username": username, "password": password},
        )
        if response.status_code != 200:
            raise RuntimeError(f"Login de {username}: HTTP {response.status_code}.")
        headers.append({"Authorization": "Bearer " + response.json()["access_token"]})
    first, second = headers
    moment = datetime.now(UTC) + timedelta(days=1)
    payload = {
        "paciente_id": 9001,
        "profissional_id": 901,
        "data_hora": moment.isoformat(),
        "status": "agendada",
        "observacao": '<script>alert("XSS")</script>',
    }
    results = []
    pause(
        "Contas autenticadas; segredos ocultos. ENTER: criar e consultar dado ficticio. "
    )
    created = client.post("/consultas", headers=first, json=payload)
    expect(created, 201, "Criacao pelo profissional vinculado")
    record_id = created.json()["id"]
    own = client.get(f"/consultas/{record_id}", headers=first)
    expect(own, 200, "Leitura pelo proprio profissional")
    public_fields = {
        "id",
        "paciente_id",
        "profissional_id",
        "data_hora",
        "status",
        "observacao",
    }
    if set(own.json()) != public_fields:
        raise RuntimeError("Campos de saida divergentes do contrato.")
    print(json.dumps(own.json(), indent=2, ensure_ascii=False), flush=True)
    print("criado_em e referencia_interna ausentes da resposta.", flush=True)
    results.append({"case": "create/read", "status": [201, 200]})

    pause("ENTER: demonstrar ownership e restricao administrativa. ")
    foreign = client.get(f"/consultas/{record_id}", headers=second)
    expect(foreign, 404, "Outro profissional tenta ler a mesma consulta")
    admin = client.get("/admin/painel", headers=first)
    expect(admin, 403, "Profissional tenta acessar painel administrativo")
    results.append({"case": "ownership/admin", "status": [404, 403]})

    pause("ENTER: demonstrar entrada, escape HTML e cabecalhos. ")
    invalid = client.post(
        "/consultas", headers=first, json={**payload, "papel": "admin"}
    )
    expect(invalid, 422, "Campo nao declarado no contrato")
    agenda = client.get(
        "/agenda", headers=first, params={"dia": moment.date().isoformat()}
    )
    expect(agenda, 200, "Agenda HTML autenticada")
    if (
        str(escape(payload["observacao"])) not in agenda.text
        or payload["observacao"] in agenda.text
    ):
        raise RuntimeError("Escape da observacao nao comprovado nesta resposta.")
    print("Observacao presente como texto escapado no HTML; sem tag script injetada.")
    print("Esta verificacao HTTP nao substitui a observacao visual no navegador.")
    for name in (
        "x-frame-options",
        "x-content-type-options",
        "content-security-policy",
    ):
        if not agenda.headers.get(name):
            raise RuntimeError(f"Cabecalho ausente: {name}")
        print(f"{name}: {agenda.headers[name]}")
    results.append({"case": "validation/html", "status": [422, 200], "escaped": True})
    print("Ensaio concluido. HSTS nao e esperado neste servidor HTTP local.")
    return results


def main():
    print("Somente API local e dados ficticios. Nao digite credenciais de producao.")
    password_one = getpass("Senha local de video_prof1 (oculta): ")
    password_two = getpass("Senha local de video_prof2 (oculta): ")
    try:
        with httpx.Client(
            base_url="http://127.0.0.1:8000", timeout=15, trust_env=False
        ) as client:
            demonstrate(client, password_one, password_two)
    except (httpx.HTTPError, RuntimeError, KeyError) as exc:
        # Nao imprimir requests completos, headers, senha ou resposta do login.
        message = str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__
        print("Ensaio interrompido:", message)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
