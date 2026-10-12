from typing import List, Optional

from fastapi import APIRouter, Depends, Request, Response, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_admin
from app.core.templating import toast
from app.models.deal import DealStage
from app.schemas.common import error_responses
from app.schemas.deal import DealCreate, DealRead, DealStageUpdate, DealUpdate
from app.services import deal_service

router = APIRouter(prefix="/api/deals", tags=["deals"])


@router.get(
    "/",
    response_model=List[DealRead],
    summary="Listar deals",
    responses=error_responses(401, 404),
)
def list_deals(
    stage: Optional[DealStage] = None,
    customer_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Deals filtrables por etapa y cliente."""
    return deal_service.list_deals(session, stage=stage, customer_id=customer_id)


@router.get(
    "/{deal_id}",
    response_model=DealRead,
    summary="Obtener un deal",
    responses=error_responses(401, 404),
)
def get_deal(
    deal_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Datos de un deal."""
    return deal_service.get_deal(session, deal_id)


@router.post(
    "/",
    response_model=DealRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear deal",
    responses=error_responses(401, 404),
)
def create_deal(
    data: DealCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Crea un deal. Una etapa cerrada fija la probabilidad (Ganado = 100, Perdido = 0)."""
    return deal_service.create_deal(session, data)


@router.patch(
    "/{deal_id}",
    response_model=DealRead,
    summary="Actualizar deal (parcial)",
    responses=error_responses(401, 404),
)
def update_deal(
    deal_id: int,
    data: DealUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Actualiza solo los campos enviados. Al reabrir un deal cerrado sin `probability`,
    toma la probabilidad base de la etapa (Prospecto 10, Contactado 30, Propuesta Enviada 60)."""
    return deal_service.update_deal(session, deal_id, data)


@router.patch(
    "/{deal_id}/stage",
    response_model=DealRead,
    summary="Mover deal de etapa",
    responses=error_responses(401, 404),
)
def change_deal_stage(
    deal_id: int,
    data: DealStageUpdate,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Mueve el deal a otra etapa aplicando las reglas de probabilidad (lo usa el Kanban)."""
    deal = deal_service.change_stage(session, deal_id, data.stage)
    # El tablero Kanban llama a este endpoint vía HTMX: se le agrega el toast
    # (HX-Trigger), que los demás clientes de la API simplemente ignoran.
    if request.headers.get("HX-Request"):
        label = deal_service.STAGE_LABELS[deal.stage]
        level = "warning" if deal.stage == DealStage.CLOSED_LOST else "success"
        toast(response, f"«{deal.title}» movido a {label}", level)
    return deal


@router.delete(
    "/{deal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar deal (admin)",
    responses=error_responses(401, 403, 404),
)
def delete_deal(
    deal_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    """Elimina un deal. Solo `admin`. Sus tareas quedan asociadas solo al cliente."""
    deal_service.delete_deal(session, deal_id)
