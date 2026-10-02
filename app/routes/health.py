from fastapi import APIRouter

from app.models.health import HealthResponse

router = APIRouter(tags=["Status"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Indica que o processo responde; nao verifica banco nem dependencias."""
    return HealthResponse(status="ok")
