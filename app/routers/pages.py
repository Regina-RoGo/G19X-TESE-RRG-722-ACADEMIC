from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user_optional
from app.core.templating import form_error, templates
from app.models.customer_insight import ChurnRisk
from app.models.deal import DealStage
from app.models.user import User
from app.repositories import (
    ai_summary_repository,
    interaction_type_repository,
    sales_suggestion_repository,
)
from app.routers import insight_pages
from app.schemas.deal import DealCreate
from app.schemas.interaction import InteractionCreate
from app.services import (
    ai_service,
    customer_service,
    customer_tag_service,
    dashboard_service,
    deal_service,
    health_service,
    interaction_service,
)

router = APIRouter(tags=["pages"])


@router.get("/")
def index(
    request: Request,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    dashboard_data = dashboard_service.get_dashboard_data(session)
    return templates.TemplateResponse(
        request,
        "index.html",
        {**dashboard_data, "current_user": current_user},
    )


@router.get("/fragments/health-check", response_class=HTMLResponse)
def health_check_fragment(session: Session = Depends(get_session)):
    status_result = health_service.get_health_status(session)
    if status_result["database"] == "ok":
        return '<span class="text-success">✅ Conexión a PostgreSQL exitosa</span>'
    return '<span class="text-error">⚠️ No se pudo conectar a la base de datos</span>'


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


def _parse_churn(churn: Optional[str]) -> Optional[ChurnRisk]:
    # Los <select> envían "" para "Todos": se trata como sin filtro en vez de un 422.
    try:
        return ChurnRisk(churn) if churn else None
    except ValueError:
        return None


def _customers_table_context(
    session: Session, q: Optional[str], tag: Optional[str], churn: Optional[str]
) -> dict:
    customers = customer_service.list_customers(
        session,
        search=q,
        tag=customer_tag_service.normalize_tag_name(tag) if tag else None,
        churn_risk=_parse_churn(churn),
    )
    return {
        "customers": customers,
        "insights": customer_service.get_latest_insights_map(session, customers),
        "filtered": bool(q or tag or churn),
    }


@router.get("/customers", response_class=HTMLResponse)
def customers_page(
    request: Request,
    q: Optional[str] = None,
    tag: Optional[str] = None,
    churn: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request,
        "customers.html",
        {
            **_customers_table_context(session, q, tag, churn),
            "query": q or "",
            "selected_tag": tag or "",
            "selected_churn": churn or "",
            "tag_names": customer_tag_service.list_tag_names(session),
            "churn_levels": list(ChurnRisk),
            "current_user": current_user,
        },
    )


@router.get("/customers/export/csv")
def export_customers_csv(
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    csv_content = customer_service.export_customers_csv(session)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clientes.csv"},
    )


@router.get("/fragments/customers-table", response_class=HTMLResponse)
def customers_table_fragment(
    request: Request,
    q: Optional[str] = None,
    tag: Optional[str] = None,
    churn: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request,
        "partials/customers_table.html",
        _customers_table_context(session, q, tag, churn),
    )


@router.get("/customers/{customer_id}", response_class=HTMLResponse)
def customer_detail_page(
    request: Request,
    customer_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    customer = customer_service.get_customer(session, customer_id)
    interactions = interaction_service.list_interactions(session, customer_id)
    interaction_types = interaction_type_repository.get_all(session)
    summary = ai_summary_repository.get_latest_by_customer(session, customer_id)
    deals = deal_service.list_deals(session, customer_id=customer_id)
    suggestion = sales_suggestion_repository.get_latest_by_customer(session, customer_id)

    return templates.TemplateResponse(
        request,
        "customer_detail.html",
        {
            "customer": customer,
            "interactions": interactions,
            "interaction_types": interaction_types,
            "summary": summary,
            "deals": deals,
            "suggestion": suggestion,
            **insight_pages.insight_context(session, customer_id),
            **insight_pages.tags_context(session, customer_id, current_user),
            **insight_pages.tasks_context(session, customer_id, current_user),
            "current_user": current_user,
        },
    )


@router.post("/fragments/customers/{customer_id}/interactions", response_class=HTMLResponse)
def create_interaction_fragment(
    request: Request,
    customer_id: int,
    notes: str = Form(...),
    interaction_type_id: int = Form(...),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    data = InteractionCreate(notes=notes, interaction_type_id=interaction_type_id)
    interaction_service.create_interaction(session, customer_id, data, current_user)

    interactions = interaction_service.list_interactions(session, customer_id)
    return templates.TemplateResponse(
        request, "partials/interactions_list.html", {"interactions": interactions}
    )


@router.post("/fragments/customers/{customer_id}/summarize", response_class=HTMLResponse)
def summarize_customer_fragment(
    request: Request,
    customer_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        customer = customer_service.get_customer(session, customer_id)
        summary = ai_service.generate_summary(session, customer)
    except (ai_service.AIServiceError, HTTPException) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        return templates.TemplateResponse(
            request, "partials/ai_summary_result.html", {"error": detail}
        )

    return templates.TemplateResponse(
        request, "partials/ai_summary_result.html", {"summary": summary}
    )


def _create_deal_from_form(
    session: Session,
    title: str,
    customer_id: int,
    value: str,
    probability: int,
    stage: DealStage,
) -> Optional[str]:
    """Crea el deal desde un formulario HTMX; devuelve un mensaje de error o None."""
    try:
        data = DealCreate(
            title=title.strip(),
            customer_id=customer_id,
            value=Decimal(value.strip() or "0"),
            probability=probability,
            stage=stage,
        )
        deal_service.create_deal(session, data)
    except (InvalidOperation, ValidationError):
        return "Revise los datos: el título es obligatorio, el monto debe ser un número ≥ 0 y la probabilidad estar entre 0 y 100."
    except HTTPException as exc:
        return exc.detail
    return None


@router.get("/pipeline", response_class=HTMLResponse)
def pipeline_page(
    request: Request,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request,
        "pipeline.html",
        {
            "columns": deal_service.get_pipeline(session),
            "customers": customer_service.list_customers(session),
            "current_user": current_user,
        },
    )


@router.get("/fragments/pipeline/board", response_class=HTMLResponse)
def pipeline_board_fragment(
    request: Request,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request, "partials/pipeline_board.html", {"columns": deal_service.get_pipeline(session)}
    )


@router.post("/fragments/deals", response_class=HTMLResponse)
def create_deal_fragment(
    request: Request,
    title: str = Form(...),
    customer_id: int = Form(...),
    value: str = Form("0"),
    probability: int = Form(0),
    stage: DealStage = Form(DealStage.PROSPECT),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    error = _create_deal_from_form(session, title, customer_id, value, probability, stage)
    if error:
        return form_error(request, error, "#deal-form-error")

    return templates.TemplateResponse(
        request, "partials/pipeline_board.html", {"columns": deal_service.get_pipeline(session)}
    )


@router.post("/fragments/customers/{customer_id}/deals", response_class=HTMLResponse)
def create_customer_deal_fragment(
    request: Request,
    customer_id: int,
    title: str = Form(...),
    value: str = Form("0"),
    probability: int = Form(0),
    stage: DealStage = Form(DealStage.PROSPECT),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    error = _create_deal_from_form(session, title, customer_id, value, probability, stage)
    if error:
        return form_error(request, error, "#customer-deal-form-error")

    deals = deal_service.list_deals(session, customer_id=customer_id)
    return templates.TemplateResponse(
        request, "partials/customer_deals_list.html", {"deals": deals}
    )


@router.post("/fragments/customers/{customer_id}/sales-suggestions", response_class=HTMLResponse)
def sales_suggestions_fragment(
    request: Request,
    customer_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        customer = customer_service.get_customer(session, customer_id)
        suggestion = ai_service.generate_sales_suggestions(session, customer)
    except (ai_service.AIServiceError, HTTPException) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        return templates.TemplateResponse(
            request, "partials/sales_suggestion_result.html", {"error": detail}
        )

    return templates.TemplateResponse(
        request, "partials/sales_suggestion_result.html", {"suggestion": suggestion}
    )
