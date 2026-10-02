from fastapi import HTTPException, Request
from pydantic import ValidationError

from app.models.entrada import CorpoVazio, LoginForm


async def login_form(request: Request) -> LoginForm:
    if (
        request.headers.get("content-type", "").split(";")[0].lower()
        != "application/x-www-form-urlencoded"
    ):
        raise HTTPException(415, "Use formulario application/x-www-form-urlencoded.")
    form = await request.form()
    if request.query_params or any(len(form.getlist(key)) != 1 for key in form):
        raise HTTPException(422, "Parametros duplicados ou inesperados.")
    try:
        return LoginForm.model_validate(dict(form))
    except ValidationError as exc:
        raise HTTPException(422, "Formulario invalido.") from exc


async def empty_body(request: Request) -> None:
    if request.query_params:
        raise HTTPException(422, "Parametros inesperados.")
    raw = await request.body()
    if not raw:
        return
    try:
        CorpoVazio.model_validate_json(raw)
    except ValidationError as exc:
        raise HTTPException(422, "Esta operacao nao aceita campos no corpo.") from exc
