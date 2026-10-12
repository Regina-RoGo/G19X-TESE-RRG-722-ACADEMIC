from typing import List

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.schemas.common import error_responses
from app.schemas.interaction import InteractionCreate, InteractionRead
from app.services import interaction_service

router = APIRouter(prefix="/api/customers/{customer_id}/interactions", tags=["interactions"])


@router.get(
    "/",
    response_model=List[InteractionRead],
    summary="Historial de interacciones del cliente",
    responses=error_responses(401, 404),
)
def list_interactions(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Interacciones del cliente, de la más reciente a la más antigua."""
    return interaction_service.list_interactions(session, customer_id)


@router.post(
    "/",
    response_model=InteractionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar interacción",
    responses=error_responses(401, 404),
)
def create_interaction(
    customer_id: int,
    data: InteractionCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Registra una interacción; el autor es siempre el usuario autenticado.

    **404** si el cliente o el tipo de interacción no existen."""
    return interaction_service.create_interaction(session, customer_id, data, current_user)
