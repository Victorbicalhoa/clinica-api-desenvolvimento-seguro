from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

from conftest import TEST_PASSWORD
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select

from app.core.config import Settings
from app.main import create_app
from app.models.usuario import Papel, Sessao, Usuario


def test_confirmacoes_mfa_simultaneas_criam_uma_sessao(password_hash):
    # Arquivo descartavel: o pool abre conexoes distintas, com lock transacional real.
    # mkdir padrao evita ACL restritiva de tmp_path no runner Windows do Assessment.
    test_dir = Path(__file__).resolve().parents[1] / ".cache" / f"mfa-test-{uuid4().hex}"
    test_dir.mkdir(parents=True)
    database = test_dir / "mfa_race.db"
    engine = create_engine(
        f"sqlite:///{database.as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    codes = {}
    app = create_app(
        engine=engine,
        settings=Settings(_env_file=None, mfa_simulated=True),
        mfa_sender=lambda challenge, code: codes.__setitem__(challenge, code),
    )
    try:
        with TestClient(app) as client:
            with Session(engine) as session:
                session.add(
                    Usuario(username="admin", password_hash=password_hash, papel=Papel.ADMIN)
                )
                session.commit()
            response = client.post(
                "/auth/token",
                data={"grant_type": "password", "username": "admin", "password": TEST_PASSWORD},
            )
            assert response.status_code == 202
            challenge = response.json()["challenge_id"]
            payload = {"challenge_id": challenge, "code": codes[challenge]}
            barrier = Barrier(2)

            def confirm():
                barrier.wait(timeout=10)
                return client.post("/auth/mfa", json=payload).status_code

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(confirm) for _ in range(2)]
                statuses = sorted(future.result(timeout=20) for future in futures)
            assert statuses == [200, 401]
            with Session(engine) as session:
                records = session.exec(select(Sessao)).all()
                assert len(records) == 1 and records[0].mfa
    finally:
        engine.dispose()
        for suffix in ("", "-journal", "-wal", "-shm"):
            file = database.with_name(database.name + suffix)
            file.unlink(missing_ok=True)
        test_dir.rmdir()
