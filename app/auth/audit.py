from fastapi import Request
from sqlmodel import Session

from app.models.integracao import EventoIntegracao
from app.models.seguranca import AcaoAuditoria, EventoAuditoria


def event(
    request: Request, action: AcaoAuditoria, status: int, resource_id: int | None = None
) -> EventoAuditoria:
    # FastAPI resolve routers incluidos de forma lazy. Usar a rota realmente despachada,
    # nao enumerar tipos internos de router nem salvar a URL recebida.
    route = request.scope.get("route")
    template = getattr(route, "path", getattr(request.state, "audit_route", "<unmatched>"))
    if resource_id is None:
        raw = request.scope.get("path_params", {}).get("consulta_id", "")
        if isinstance(raw, str) and raw.isascii() and raw.isdecimal() and len(raw) <= 10:
            candidate = int(raw)
            if 1 <= candidate <= 2_147_483_647:
                resource_id = candidate
    return EventoAuditoria(
        request_id=request.state.request_id,
        ator_id=getattr(request.state, "audit_actor", None),
        acao=action,
        rota=template,
        metodo=request.method,
        recurso_id=resource_id,
        status_http=status,
        alerta=status == 429,
    )


def mutation(
    session: Session, request: Request, action: AcaoAuditoria, status: int, resource_id: int
) -> None:
    # Add apenas: quem altera o recurso confirma ambos na MESMA transacao.
    session.add(event(request, action, status, resource_id))


def record_request(request: Request, status: int) -> None:
    with Session(request.app.state.engine) as session:
        client_id = getattr(request.state, "machine_id", None)
        if client_id is not None:
            route = request.scope.get("route")
            session.add(
                EventoIntegracao(
                    request_id=request.state.request_id,
                    client_id=client_id,
                    rota=getattr(
                        route, "path", getattr(request.state, "audit_route", "<unmatched>")
                    ),
                    status_http=status,
                )
            )
        session.add(
            event(
                request, AcaoAuditoria.HTTP, status, getattr(request.state, "audit_resource", None)
            )
        )
        session.commit()
