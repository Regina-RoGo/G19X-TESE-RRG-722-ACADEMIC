from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_admin
from app.schemas.ai_summary import AISummaryRead
from app.schemas.common import error_responses
from app.models.customer_insight import ChurnRisk
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.schemas.customer_insight import CustomerInsightRead
from app.schemas.customer_tag import CustomerTagCreate, CustomerTagRead
from app.schemas.sales_suggestion import SalesSuggestionRead
from app.services import ai_service, customer_service, customer_tag_service

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get(
    "/",
    response_model=List[CustomerRead],
    summary="Listar clientes",
    responses=error_responses(401),
)
def list_customers(
    q: Optional[str] = None,
    tag: Optional[str] = None,
    churn: Optional[ChurnRisk] = None,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """`tag` filtra por tag aplicado; `churn` por el riesgo del análisis IA más reciente."""
    return customer_service.list_customers(
        session,
        search=q,
        tag=customer_tag_service.normalize_tag_name(tag) if tag else None,
        churn_risk=churn,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
    summary="Obtener un cliente",
    responses=error_responses(401, 404),
)
def get_customer(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Datos base de un cliente."""
    return customer_service.get_customer(session, customer_id)


@router.post(
    "/",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cliente (admin)",
    responses=error_responses(401, 403),
)
def create_customer(
    data: CustomerCreate,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    """Crea un cliente. Solo `admin`."""
    return customer_service.create_customer(session, data)


@router.put(
    "/{customer_id}",
    response_model=CustomerRead,
    summary="Actualizar cliente (admin)",
    responses=error_responses(401, 403, 404),
)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    """Reemplaza los datos del cliente. Solo `admin`."""
    return customer_service.update_customer(session, customer_id, data)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar cliente (admin)",
    responses=error_responses(401, 403, 404, 409),
)
def delete_customer(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    """Elimina un cliente sin actividad. Solo `admin`.

    Responde **409** si tiene deals, interacciones, tareas o resultados de IA asociados
    (se conserva el historial comercial). Sus tags se eliminan con él."""
    customer_service.delete_customer(session, customer_id)


@router.post(
    "/{customer_id}/summarize",
    response_model=AISummaryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generar resumen ejecutivo con IA",
    responses=error_responses(400, 401, 404, 502),
)
def summarize_customer(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Genera con Gemini un resumen ejecutivo del historial de interacciones y su sentimiento
    (POSITIVO/NEUTRAL/NEGATIVO), y lo guarda.

    **400** si el cliente no tiene interacciones; **502** si Gemini falla tras el reintento."""
    customer = customer_service.get_customer(session, customer_id)
    try:
        return ai_service.generate_summary(session, customer)
    except ai_service.AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post(
    "/{customer_id}/sales-suggestions",
    response_model=SalesSuggestionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generar sugerencias de venta con IA",
    responses=error_responses(400, 401, 404, 502),
)
def generate_sales_suggestions(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Genera con Gemini próximos pasos priorizados y una estrategia de cierre a partir de las
    interacciones y los deals del cliente, y los guarda.

    **400** si el cliente no tiene interacciones; **502** si Gemini falla tras el reintento."""
    customer = customer_service.get_customer(session, customer_id)
    try:
        return ai_service.generate_sales_suggestions(session, customer)
    except ai_service.AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get(
    "/{customer_id}/insights",
    response_model=CustomerInsightRead,
    summary="Último análisis predictivo",
    responses=error_responses(401, 404),
)
def get_latest_insights(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Último análisis predictivo guardado (lead score, churn, tags y tareas sugeridas).

    **404** si el cliente aún no tiene análisis. No llama a Gemini."""
    customer = customer_service.get_customer(session, customer_id)
    return ai_service.get_latest_insights(session, customer)


@router.post(
    "/{customer_id}/insights",
    response_model=CustomerInsightRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generar análisis predictivo con IA",
    responses=error_responses(400, 401, 404, 502),
)
def generate_insights(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Genera con Gemini, en una sola llamada, lead score (0–100), riesgo de churn
    (BAJO/MEDIO/ALTO), tags y tareas sugeridas, y los guarda. Las tareas sugeridas no se crean solas.

    **400** si el cliente no tiene interacciones; **502** si Gemini falla tras el reintento."""
    customer = customer_service.get_customer(session, customer_id)
    try:
        return ai_service.generate_insights(session, customer)
    except ai_service.AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get(
    "/{customer_id}/tags",
    response_model=List[CustomerTagRead],
    summary="Listar tags del cliente",
    responses=error_responses(401, 404),
)
def list_customer_tags(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Tags aplicados al cliente, ordenados por nombre."""
    return customer_tag_service.list_tags(session, customer_id)


@router.post(
    "/{customer_id}/tags",
    response_model=CustomerTagRead,
    status_code=status.HTTP_201_CREATED,
    summary="Aplicar tag al cliente",
    responses=error_responses(401, 404, 409),
)
def add_customer_tag(
    customer_id: int,
    data: CustomerTagCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Aplica un tag (se normaliza a minúsculas). **409** si el cliente ya lo tiene."""
    return customer_tag_service.add_tag(session, customer_id, data.name, data.source)


@router.delete(
    "/{customer_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quitar tag del cliente (admin)",
    responses=error_responses(401, 403, 404),
)
def remove_customer_tag(
    customer_id: int,
    tag_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    """Quita un tag del cliente. Solo `admin`."""
    customer_tag_service.remove_tag(session, customer_id, tag_id)
