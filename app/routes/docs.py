from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.templates import templates

router = APIRouter(include_in_schema=False)


@router.get("/docs", response_class=HTMLResponse)
def docs(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="docs.html",
        context={
            "openapi_url": request.scope.get("root_path", "") + "/openapi.json",
        },
    )


@router.get("/redoc")
def redoc_redirect(request: Request):
    return RedirectResponse(request.url_for("docs"), status_code=307)
