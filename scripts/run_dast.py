"""ZAP passivo real sobre corpus autenticado, somente em loopback descartavel."""

import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from sqlalchemy.engine import URL
from sqlmodel import Session

from app.auth.security import hash_password
from app.core.config import Settings
from app.database.session import build_engine, create_tables
from app.main import create_app
from app.models.integracao import ClienteIntegracao, ClienteProfissional, SlotOferta
from app.models.usuario import Papel, Usuario, VinculoPaciente


def make_app():
    return create_app(
        settings=Settings(
            _env_file=None,
            database_url=os.environ["DAST_DB"],
            jwt_secret=os.environ["DAST_JWT"],
            mfa_simulated=False,
        )
    )


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for(call, processes, seconds=120):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            raise RuntimeError("Processo local encerrou antes de completar o scan")
        try:
            value = call()
            if value:
                return value
        except (httpx.HTTPError, ValueError):
            pass
        time.sleep(0.5)
    raise TimeoutError("Scan local nao completou no prazo")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zap-home", type=Path, required=True)
    parser.add_argument("--java", default="java")
    args = parser.parse_args()
    cache = Path(".cache") / ("dast-" + secrets.token_hex(8))
    cache = cache.resolve()
    cache.mkdir(parents=True)
    zap_data = cache / "zap"
    zap_data.mkdir()
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    (reports / "zap.json").unlink(missing_ok=True)  # Nunca reutilizar resultado antigo.
    url = URL.create("sqlite", database=str(cache / "dast.db")).render_as_string()
    settings = Settings(_env_file=None, database_url=url)
    engine = build_engine(settings)
    password = secrets.token_urlsafe(24)
    try:
        create_tables(engine)
        with Session(engine) as session:
            hashed = hash_password(password)
            session.add(
                Usuario(
                    id=1,
                    username="dast_prof",
                    password_hash=hashed,
                    papel=Papel.PROFISSIONAL,
                    profissional_id=2,
                )
            )
            session.add(
                Usuario(
                    id=2, username="dast_recepcao", password_hash=hashed, papel=Papel.RECEPCIONISTA
                )
            )
            session.flush()
            session.add(VinculoPaciente(usuario_id=1, paciente_id=1))
            session.add(ClienteIntegracao(client_id="dast_lab", secret_hash=hashed))
            session.flush()
            session.add(ClienteProfissional(client_id="dast_lab", profissional_id=2))
            session.add(
                SlotOferta(profissional_id=2, inicio=datetime(2030, 10, 15, 13, tzinfo=UTC))
            )
            session.commit()
    finally:
        engine.dispose()
    port, proxy_port = free_port(), free_port()
    target, proxy = f"http://127.0.0.1:{port}", f"http://127.0.0.1:{proxy_port}"
    api_key = secrets.token_urlsafe(32)
    child_env = {
        key: value for key, value in os.environ.items() if key.lower() not in Settings.model_fields
    }
    child_env.update(DAST_DB=url, DAST_JWT=secrets.token_urlsafe(48), PYTHONIOENCODING="utf-8")
    server_python = sys.executable
    if os.name == "nt":
        # Evita o launcher da venv criar um neto fora do handle Popen no Windows.
        server_python = sys._base_executable
        child_env["PYTHONPATH"] = os.pathsep.join(str(Path(p).resolve()) for p in sys.path if p)
    processes = []
    flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    with (cache / "server.log").open("wb") as server_log, (cache / "zap.log").open("wb") as zap_log:
        try:
            processes.append(
                subprocess.Popen(
                    [
                        server_python,
                        "-m",
                        "uvicorn",
                        "scripts.run_dast:make_app",
                        "--factory",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                        "--no-access-log",
                    ],
                    env=child_env,
                    stdout=server_log,
                    stderr=subprocess.STDOUT,
                    **flags,
                )
            )
            jar = args.zap_home.resolve() / "zap-2.17.0.jar"
            processes.append(
                subprocess.Popen(
                    [
                        args.java,
                        "-Xmx512m",
                        "-jar",
                        str(jar),
                        "-daemon",
                        "-host",
                        "127.0.0.1",
                        "-port",
                        str(proxy_port),
                        "-dir",
                        str(zap_data),
                        "-config",
                        f"api.key={api_key}",
                        "-config",
                        "autoupdate.checkOnStart=false",
                        "-silent",
                    ],
                    stdout=zap_log,
                    stderr=subprocess.STDOUT,
                    **flags,
                )
            )
            with httpx.Client(trust_env=False, timeout=10) as direct:

                def api(component, kind, name, **params):
                    response = direct.get(
                        f"{proxy}/JSON/{component}/{kind}/{name}/",
                        params={"apikey": api_key, **params},
                    )
                    response.raise_for_status()
                    return response.json()

                wait_for(lambda: direct.get(target + "/health").status_code == 200, processes)
                version = wait_for(lambda: api("core", "view", "version").get("version"), processes)

                def login(username):
                    response = direct.post(
                        target + "/auth/token",
                        data={"grant_type": "password", "username": username, "password": password},
                    )
                    response.raise_for_status()
                    return {"Authorization": "Bearer " + response.json()["access_token"]}

                professional, reception = login("dast_prof"), login("dast_recepcao")
                machine_response = direct.post(
                    target + "/integracoes/token",
                    auth=("dast_lab", password),
                    data={"grant_type": "client_credentials", "scope": "disponibilidade:read"},
                )
                machine_response.raise_for_status()
                machine = {"Authorization": "Bearer " + machine_response.json()["access_token"]}
                created = direct.post(
                    target + "/consultas",
                    headers=professional,
                    json={
                        "paciente_id": 1,
                        "profissional_id": 2,
                        "data_hora": "2030-10-15T12:00:00Z",
                        "status": "agendada",
                        "observacao": "Dado inteiramente ficticio do scan",
                    },
                )
                created.raise_for_status()
                corpus = [
                    ("health", "/health", {}, 200),
                    ("docs", "/docs", {}, 200),
                    ("openapi", "/openapi.json", {}, 200),
                    ("consulta-list", "/consultas", professional, 200),
                    ("consulta-detail", f"/consultas/{created.json()['id']}", professional, 200),
                    ("agenda-prof", "/agenda?dia=2030-10-15", professional, 200),
                    ("agenda-recepcao", "/agenda?dia=2030-10-15", reception, 200),
                    ("admin-denied", "/admin/painel", professional, 403),
                    ("unauth-denied", "/consultas", {}, 401),
                    (
                        "machine-availability",
                        "/integracoes/disponibilidade?dia=2030-10-15",
                        machine,
                        200,
                    ),
                    ("machine-human-denied", "/consultas", machine, 401),
                    (
                        "human-machine-denied",
                        "/integracoes/disponibilidade?dia=2030-10-15",
                        professional,
                        401,
                    ),
                ]
                coverage = []
                with httpx.Client(proxy=proxy, trust_env=False, timeout=20) as scanner:
                    for identifier, path, headers, expected in corpus:
                        response = scanner.get(target + path, headers=headers)
                        coverage.append(
                            {
                                "id": identifier,
                                "path": path,
                                "status": response.status_code,
                                "expected": expected,
                            }
                        )
                        if response.status_code != expected:
                            raise RuntimeError("Corpus DAST nao atingiu resultado esperado")
                # Aguarda fila passiva esvaziar e estabilizar antes de ler os alertas.
                time.sleep(2)
                wait_for(
                    lambda: int(api("pscan", "view", "recordsToScan")["recordsToScan"]) == 0,
                    processes,
                )
                time.sleep(1)
                remaining = int(api("pscan", "view", "recordsToScan")["recordsToScan"])
                if remaining:
                    raise RuntimeError("Fila passiva incompleta")
                raw = api("core", "view", "alerts", baseurl=target, start=0, count=10000)["alerts"]
                # Whitelist: nunca exportar mensagens HTTP, tokens, cookies ou evidencias brutas.
                alerts = [
                    {
                        "path": urlsplit(alert["url"]).path,
                        **{
                            key: str(alert.get(key, ""))
                            for key in (
                                "pluginId",
                                "alert",
                                "risk",
                                "confidence",
                                "cweid",
                                "wascid",
                                "method",
                            )
                        },
                    }
                    for alert in raw
                ]
                result = {
                    "schema_version": 1,
                    "mode": "passive-authenticated-corpus",
                    "zap_version": version,
                    "records_to_scan": remaining,
                    "coverage": coverage,
                    "alerts": alerts,
                    "limits": "HTTP loopback; sem TLS/spider/active scan/IAST; dados ficticios",
                }
                print(
                    f"ZAP {version}: {len(coverage)} respostas; {len(alerts)} alertas; fila vazia."
                )
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
            # Arquivos de scan sao descartaveis; nunca incluir .cache no artifact/ZIP.
            for name in ("dast.db", "dast.db-journal", "dast.db-wal", "dast.db-shm"):
                (cache / name).unlink(missing_ok=True)
    (reports / "zap.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
