from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.services import health_service

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check(session: Session = Depends(get_session)) -> dict:
    return health_service.get_health_status(session)
