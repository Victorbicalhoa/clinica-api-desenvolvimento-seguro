"""Provisionamento local confiavel: clientes, revogacao e oferta de horarios."""

import argparse
import re
from datetime import UTC, datetime
from getpass import getpass

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth.security import hash_password
from app.database.session import build_engine, create_tables
from app.models.entrada import USERNAME_PATTERN
from app.models.integracao import ClienteIntegracao, ClienteProfissional, SlotOferta
from app.models.usuario import Papel, Usuario


def main():
    parser = argparse.ArgumentParser(description="Somente operador local autorizado.")
    commands = parser.add_subparsers(dest="command", required=True)
    client = commands.add_parser("client")
    client.add_argument("client_id")
    client.add_argument("--profissional-id", type=int, action="append", required=True)
    revoke = commands.add_parser("revoke")
    revoke.add_argument("client_id")
    slot = commands.add_parser("slot")
    slot.add_argument("--profissional-id", type=int, required=True)
    slot.add_argument("--inicio", required=True, help="ISO8601 com fuso; instante ofertado.")
    args = parser.parse_args()
    if args.command != "slot" and not re.fullmatch(USERNAME_PATTERN, args.client_id):
        parser.error("Client ID invalido.")
    engine = build_engine()
    try:
        create_tables(engine)
        with Session(engine) as session:
            if args.command == "revoke":
                record = session.get(ClienteIntegracao, args.client_id)
                if record is None:
                    parser.error("Cliente inexistente.")
                record.ativo = False
                record.token_version += 1
                session.add(record)
            else:
                ids = set(
                    args.profissional_id if args.command == "client" else [args.profissional_id]
                )
                for pid in ids:
                    if (
                        not 0 < pid <= 2_147_483_647
                        or session.exec(
                            select(Usuario).where(
                                Usuario.profissional_id == pid,
                                Usuario.ativo.is_(True),
                                Usuario.papel == Papel.PROFISSIONAL,
                            )
                        ).first()
                        is None
                    ):
                        parser.error("Profissional ativo inexistente.")
                if args.command == "client":
                    if session.get(ClienteIntegracao, args.client_id):
                        parser.error("Cliente ja existe; nenhuma alteracao realizada.")
                    secret = getpass("Segredo exclusivo M2M (32 a 72 bytes ASCII): ")
                    if not secret.isascii() or not 32 <= len(secret) <= 72:
                        parser.error("Segredo fora do contrato.")
                    if secret != getpass("Confirme: "):
                        parser.error("Segredos diferentes.")
                    session.add(
                        ClienteIntegracao(
                            client_id=args.client_id, secret_hash=hash_password(secret)
                        )
                    )
                    session.flush()
                    for pid in ids:
                        session.add(
                            ClienteProfissional(client_id=args.client_id, profissional_id=pid)
                        )
                else:
                    try:
                        instant = datetime.fromisoformat(args.inicio)
                        if instant.tzinfo is None:
                            raise ValueError
                        instant = instant.astimezone(UTC)
                        if instant <= datetime.now(UTC):
                            raise ValueError
                    except (ValueError, OverflowError):
                        parser.error("Inicio futuro deve usar ISO8601 com fuso.")
                    session.add(SlotOferta(profissional_id=args.profissional_id, inicio=instant))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                parser.error("Registro duplicado; nenhuma alteracao confirmada.")
        print("Operacao concluida. Nenhum segredo foi impresso.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
