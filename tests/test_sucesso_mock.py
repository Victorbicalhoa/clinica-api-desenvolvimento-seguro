"""Complementa o sucesso integrado do Ex1; mocks nao substituem a integracao."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec

from fastapi import Request, Response
from sqlmodel import Session

from app.models.consulta import ConsultaRead, ConsultaWrite
from app.models.seguranca import AcaoAuditoria, EventoAuditoria
from app.models.usuario import Papel, Usuario, VinculoPaciente
from app.routes.consultas import criar_consulta, obter_consulta


def test_criar_e_buscar_consulta_com_session_mock(consulta_payload):
    session = create_autospec(Session, instance=True)
    user = Usuario(
        id=7,
        username="unit",
        profissional_id=2,
        papel=Papel.PROFISSIONAL,
        password_hash="somente-mock",
    )
    session.get.return_value = VinculoPaciente(usuario_id=7, paciente_id=1)
    request = MagicMock(spec=Request)
    request.state = SimpleNamespace(request_id="requisicao-mock", audit_actor=7)
    request.scope = {"route": SimpleNamespace(path="/consultas")}
    request.method = "POST"

    def assign_generated_id():
        session.add.call_args_list[0].args[0].id = 123

    session.flush.side_effect = assign_generated_id
    data = ConsultaWrite.model_validate(consulta_payload)
    response = Response()
    created = criar_consulta(data, response, session, user, request)
    session.get.assert_called_once_with(VinculoPaciente, (7, 1))
    session.commit.assert_called_once()
    session.rollback.assert_not_called()
    session.refresh.assert_called_once_with(created)
    audit_event = session.add.call_args_list[1].args[0]
    assert isinstance(audit_event, EventoAuditoria)
    assert audit_event.acao == AcaoAuditoria.CRIAR and audit_event.recurso_id == 123
    assert request.state.audit_written is True
    assert response.headers["Location"] == "/consultas/123"
    session.exec.return_value.first.return_value = created
    read = obter_consulta(123, session, user)
    exposed = ConsultaRead.model_validate(read).model_dump()
    assert exposed["id"] == 123 and exposed["paciente_id"] == 1
    assert exposed["data_hora"] == datetime(2030, 10, 15, 12, tzinfo=UTC)
    assert set(exposed) == {
        "id",
        "paciente_id",
        "profissional_id",
        "data_hora",
        "status",
        "observacao",
    }
    assert session.exec.call_count == 1
