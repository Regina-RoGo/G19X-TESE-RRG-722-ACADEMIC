from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_admin
from app.schemas.ai_summary import AISummaryRead
from app.models.customer_insight import ChurnRisk
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.schemas.customer_insight import CustomerInsightRead
from app.schemas.customer_tag import CustomerTagCreate, CustomerTagRead
from app.schemas.sales_suggestion import SalesSuggestionRead
from app.services import ai_service, customer_service, customer_tag_service

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/", response_model=List[CustomerRead])
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


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return customer_service.get_customer(session, customer_id)


@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreate,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    return customer_service.create_customer(session, data)


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    return customer_service.update_customer(session, customer_id, data)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    customer_service.delete_customer(session, customer_id)


@router.post("/{customer_id}/summarize", response_model=AISummaryRead, status_code=status.HTTP_201_CREATED)
def summarize_customer(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    customer = customer_service.get_customer(session, customer_id)
    try:
        return ai_service.generate_summary(session, customer)
    except ai_service.AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post(
    "/{customer_id}/sales-suggestions",
    response_model=SalesSuggestionRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_sales_suggestions(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    customer = customer_service.get_customer(session, customer_id)
    try:
        return ai_service.generate_sales_suggestions(session, customer)
    except ai_service.AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get("/{customer_id}/insights", response_model=CustomerInsightRead)
def get_latest_insights(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    customer = customer_service.get_customer(session, customer_id)
    return ai_service.get_latest_insights(session, customer)


@router.post(
    "/{customer_id}/insights",
    response_model=CustomerInsightRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_insights(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    customer = customer_service.get_customer(session, customer_id)
    try:
        return ai_service.generate_insights(session, customer)
    except ai_service.AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get("/{customer_id}/tags", response_model=List[CustomerTagRead])
def list_customer_tags(
    customer_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return customer_tag_service.list_tags(session, customer_id)


@router.post(
    "/{customer_id}/tags",
    response_model=CustomerTagRead,
    status_code=status.HTTP_201_CREATED,
)
def add_customer_tag(
    customer_id: int,
    data: CustomerTagCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return customer_tag_service.add_tag(session, customer_id, data.name, data.source)


@router.delete("/{customer_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_customer_tag(
    customer_id: int,
    tag_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    customer_tag_service.remove_tag(session, customer_id, tag_id)
