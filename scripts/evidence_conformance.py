"""Reproduz laboratorio e M2M apenas sobre fixtures descartaveis de teste."""

import json
from contextlib import contextmanager
from pathlib import Path

from app.auth.security import hash_password
from tests.conftest import TEST_PASSWORD, raw_client
from tests.test_exercicio07 import SECRET, machine_client, token
from tests.test_lab_isolado import compare_before_after


def main():
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    client_fixture = contextmanager(raw_client.__wrapped__)
    hashed = hash_password(TEST_PASSWORD)
    with client_fixture(hashed) as client:
        result = compare_before_after(client)
    (reports / "lab-before-after.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with client_fixture(hashed) as client:
        machine_client.__wrapped__(client, hash_password(SECRET))
        login = token(client)
        assert login.status_code == 200
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        available = client.get("/integracoes/disponibilidade?dia=2030-10-15", headers=headers)
        denied = client.get("/consultas", headers=headers)
        assert available.status_code == 200 and denied.status_code == 401
        result = {
            "fixture": "fictitious-memory-only",
            "token_status": login.status_code,
            "token_scope": login.json()["scope"],
            "ttl": login.json()["expires_in"],
            "availability_status": available.status_code,
            "availability": available.json(),
            "human_route_status": denied.status_code,
            "credentials_exported": False,
        }
    (reports / "m2m-evidence.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Evidencias BOLA/XSS e M2M geradas; nenhum token/segredo exportado.")


if __name__ == "__main__":
    main()
