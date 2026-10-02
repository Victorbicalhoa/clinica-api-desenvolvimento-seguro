"""Cliente de ensaio local que nunca imprime o JWT ou o segredo M2M."""

import argparse
import json
from getpass import getpass

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dia", required=True, help="Dia UTC da oferta ficticia provisionada")
    args = parser.parse_args()
    secret = getpass("Segredo de laboratorio_demo (oculto): ")
    try:
        with httpx.Client(base_url="http://127.0.0.1:8000", trust_env=False, timeout=15) as client:
            token = client.post(
                "/integracoes/token",
                auth=("laboratorio_demo", secret),
                data={"grant_type": "client_credentials", "scope": "disponibilidade:read"},
            )
            if token.status_code != 200:
                raise RuntimeError(f"Token: HTTP {token.status_code}")
            body = token.json()
            headers = {"Authorization": "Bearer " + body["access_token"]}
            print(f"Client Credentials: HTTP 200; scope={body['scope']}; TTL={body['expires_in']}s")
            input("Credenciais ocultas. ENTER: consultar disponibilidade e tentar rota clinica. ")
            available = client.get("/integracoes/disponibilidade", params={"dia": args.dia}, headers=headers)
            if available.status_code != 200:
                raise RuntimeError(f"Disponibilidade: HTTP {available.status_code}")
            rows = available.json()
            if not rows or any(set(row) != {"profissional_id", "inicio"} for row in rows):
                raise RuntimeError("Provisionar oferta futura para demonstrar o contrato minimo.")
            print("Disponibilidade: HTTP 200")
            print(json.dumps(rows, indent=2, ensure_ascii=False))
            denied = client.get("/consultas", headers=headers)
            if denied.status_code != 401:
                raise RuntimeError(f"Isolamento M2M: HTTP {denied.status_code}")
            print("Mesmo token na rota clinica /consultas: HTTP 401")
    except (httpx.HTTPError, RuntimeError, KeyError, ValueError) as exc:
        print(str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
