from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlmodel import select

from app.auth.dependencies import AgendaUserDep
from app.auth.policies import scope_consultas
from app.core.templates import templates
from app.database.session import SessionDep
from app.models.consulta import Consulta, ConsultaRead
from app.models.usuario import Papel

router = APIRouter(tags=["Agenda"])
PAGE_SIZE = 50


def hoje_utc() -> date:
    return datetime.now(UTC).date()


@router.get("/agenda", response_class=HTMLResponse)
def agenda(
    request: Request,
    user: AgendaUserDep,
    session: SessionDep,
    hoje: Annotated[date, Depends(hoje_utc)],
    dia: date | None = None,
    pagina: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
):
    dia_agenda = dia if dia is not None else hoje
    if dia_agenda == date.max:
        raise HTTPException(status_code=422, detail="Data fora do intervalo da agenda.")
    inicio = datetime.combine(dia_agenda, time.min, tzinfo=UTC)
    fim = inicio + timedelta(days=1)
    statement = (
        select(Consulta)
        .where(Consulta.data_hora >= inicio, Consulta.data_hora < fim)
        .order_by(Consulta.data_hora, Consulta.id)
        .offset((pagina - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE + 1)
    )
    if user.papel == Papel.PROFISSIONAL:
        statement = scope_consultas(statement, user)
    registros = session.exec(statement).all()
    # A mesma allowlist do JSON limita o contexto HTML; o ORM nao chega ao template.
    consultas = [ConsultaRead.model_validate(item) for item in registros[:PAGE_SIZE]]
    if user.papel == Papel.RECEPCIONISTA:
        # Recepcao ve agenda operacional; texto livre clinico nao vai ao contexto HTML.
        consultas = [item.model_copy(update={"observacao": ""}) for item in consultas]
    return templates.TemplateResponse(
        request=request,
        name="agenda.html",
        context={
            "consultas": consultas,
            "dia": dia_agenda,
            "pagina": pagina,
            "tem_proxima": len(registros) > PAGE_SIZE and pagina < 1_000_000,
        },
        headers={"Cache-Control": "no-store"},
    )
