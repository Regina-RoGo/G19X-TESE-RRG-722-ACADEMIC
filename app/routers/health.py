from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session

from app.core.database import get_session
from app.services import health_service

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "ok", "database": "ok"}]}
    )

    status: str
    database: str


@router.get("/health", response_model=HealthResponse, summary="Estado del servicio")
def health_check(session: Session = Depends(get_session)) -> dict:
    """Siempre responde 200; `database` es `ok` o `error` según la conexión a PostgreSQL."""
    return health_service.get_health_status(session)
