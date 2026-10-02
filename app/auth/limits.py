import hashlib
import math

from fastapi import HTTPException
from sqlalchemy import case
from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Session

from app.models.seguranca import OrcamentoAuth


def consume(session: Session, kind: str, value: str, limit: int, window: int, now: float) -> None:
    # Hash estavel entre workers. Pseudonimo, nao anonimato ou segredo criptografico.
    key = hashlib.sha256(f"{kind}:{value}".encode()).hexdigest()
    bucket = int(now) // window
    statement = insert(OrcamentoAuth).values(chave=key, janela=bucket, tentativas=1)
    statement = statement.on_conflict_do_update(
        index_elements=[OrcamentoAuth.chave],
        set_={
            "janela": bucket,
            "tentativas": case(
                (OrcamentoAuth.janela == bucket, OrcamentoAuth.tentativas + 1),
                else_=1,
            ),
        },
    ).returning(OrcamentoAuth.tentativas)
    count = session.exec(statement).scalar_one()
    # O orcamento nao volta quando a autenticacao ou o desafio falha.
    session.commit()
    if count > limit:
        retry = max(1, math.ceil((bucket + 1) * window - now))
        raise HTTPException(
            429, "Limite temporario de requisicoes atingido.", headers={"Retry-After": str(retry)}
        )
