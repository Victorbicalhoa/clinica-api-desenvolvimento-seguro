"""Provisionamento local confiavel: python -m app.auth.provision --help."""

import argparse
import re
from getpass import getpass

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth.security import hash_password
from app.database.session import build_engine, create_tables
from app.models.entrada import USERNAME_PATTERN
from app.models.usuario import Papel, Usuario, VinculoPaciente


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cria conta local; senha lida sem eco, nunca por argumento."
    )
    parser.add_argument("username")
    parser.add_argument("--papel", choices=list(Papel), required=True)
    parser.add_argument("--profissional-id", type=int)
    parser.add_argument("--paciente-id", type=int, action="append", default=[])
    args = parser.parse_args()
    if not re.fullmatch(USERNAME_PATTERN, args.username):
        parser.error(
            "Username ASCII: letras, numeros, ponto, hifen e sublinhado; ate 100 caracteres."
        )
    if args.papel == Papel.PROFISSIONAL:
        if args.profissional_id is None or not 0 < args.profissional_id <= 2_147_483_647:
            parser.error("Profissional requer --profissional-id positivo.")
    elif args.profissional_id is not None or args.paciente_id:
        parser.error("Apenas profissionais podem ter vinculos clinicos.")
    if any(not 0 < item <= 2_147_483_647 for item in args.paciente_id):
        parser.error("Paciente ID fora do intervalo.")
    password = getpass("Senha (12 caracteres, ate 72 bytes UTF-8): ")
    if password != getpass("Confirme a senha: "):
        parser.error("Senhas diferentes.")
    try:
        hashed = hash_password(password)
    except ValueError as exc:
        parser.error(str(exc))
    engine = build_engine()
    try:
        create_tables(engine)
        with Session(engine) as session:
            if session.exec(select(Usuario).where(Usuario.username == args.username)).first():
                parser.error("Usuario ja existe; nenhuma alteracao realizada.")
            user = Usuario(
                username=args.username,
                papel=Papel(args.papel),
                profissional_id=args.profissional_id,
                password_hash=hashed,
            )
            try:
                session.add(user)
                session.flush()
                for patient in set(args.paciente_id):
                    session.add(VinculoPaciente(usuario_id=user.id, paciente_id=patient))
                session.commit()
            except IntegrityError:
                session.rollback()
                parser.error("Usuario ou profissional ja vinculado.")
            print("Conta e vinculos criados. Nenhuma senha foi impressa ou salva em texto plano.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
