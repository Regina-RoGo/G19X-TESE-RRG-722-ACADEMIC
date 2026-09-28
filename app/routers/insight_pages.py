"""Fragmentos HTMX de la ficha del cliente para la Fase 6: analítica IA, tags y tareas."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user_optional
from app.core.templating import form_error, templates
from app.models.customer_tag import TagSource
from app.models.deal import DealStage
from app.models.task import TaskPriority
from app.models.user import User, UserRole
from app.repositories import customer_insight_repository, user_repository
from app.schemas.task import TaskCreate
from app.services import (
    ai_service,
    customer_service,
    customer_tag_service,
    deal_service,
    task_service,
)

router = APIRouter(tags=["pages"])

CLOSED_STAGES = (DealStage.CLOSED_WON, DealStage.CLOSED_LOST)


def insight_context(session: Session, customer_id: int) -> dict:
    return {"insight": customer_insight_repository.get_latest_by_customer(session, customer_id)}


def tags_context(session: Session, customer_id: int, current_user: User) -> dict:
    tags = customer_tag_service.list_tags(session, customer_id)
    insight = customer_insight_repository.get_latest_by_customer(session, customer_id)
    applied = {tag.name for tag in tags}
    return {
        "customer_id": customer_id,
        "tags": tags,
        # Tags sugeridos por el último análisis que todavía no se aplicaron.
        "available_tags": [t for t in (insight.suggested_tags if insight else []) if t not in applied],
        "can_remove_tags": current_user.role == UserRole.ADMIN,
    }


def tasks_context(session: Session, customer_id: int, current_user: User) -> dict:
    tasks = task_service.list_tasks(session, customer_id=customer_id)
    insight = customer_insight_repository.get_latest_by_customer(session, customer_id)
    # Una sugerencia se considera convertida si ya existe una tarea con el mismo título.
    existing_titles = {task.title.strip().lower() for task in tasks}
    suggested_tasks = [
        {
            **suggestion,
            "due_label": date.fromisoformat(suggestion["due_date"]).strftime("%d/%m/%Y"),
            "created": suggestion["title"].strip().lower() in existing_titles,
        }
        for suggestion in (insight.suggested_tasks if insight else [])
    ]
    is_admin = current_user.role == UserRole.ADMIN
    return {
        "customer_id": customer_id,
        "tasks": tasks,
        "suggested_tasks": suggested_tasks,
        "open_deals": [
            deal
            for deal in deal_service.list_deals(session, customer_id=customer_id)
            if deal.stage not in CLOSED_STAGES
        ],
        # Solo admin puede asignar a otra persona: el comercial no ve el selector.
        "assignable_users": user_repository.get_all(session) if is_admin else [],
        "current_user": current_user,
    }


def _redirect_to_login():
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


# --- Analítica IA -----------------------------------------------------------


@router.post("/fragments/customers/{customer_id}/insights", response_class=HTMLResponse)
def generate_insights_fragment(
    request: Request,
    customer_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return _redirect_to_login()

    try:
        customer = customer_service.get_customer(session, customer_id)
        insight = ai_service.generate_insights(session, customer)
    except (ai_service.AIServiceError, HTTPException) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        return templates.TemplateResponse(
            request, "partials/insight_result.html", {"error": detail}
        )

    # Además del resultado, se refrescan (out-of-band) las secciones de tags y
    # tareas, porque dependen de las sugerencias del nuevo análisis.
    return templates.TemplateResponse(
        request,
        "partials/insight_generate_response.html",
        {
            "insight": insight,
            **tags_context(session, customer_id, current_user),
            **tasks_context(session, customer_id, current_user),
            "oob": True,
        },
    )


# --- Tags -------------------------------------------------------------------


def _render_tags(request: Request, session: Session, customer_id: int, current_user: User):
    return templates.TemplateResponse(
        request, "partials/customer_tags.html", tags_context(session, customer_id, current_user)
    )


@router.post("/fragments/customers/{customer_id}/tags", response_class=HTMLResponse)
def add_tag_fragment(
    request: Request,
    customer_id: int,
    name: str = Form(""),
    source: TagSource = Form(TagSource.MANUAL),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return _redirect_to_login()

    try:
        customer_tag_service.add_tag(session, customer_id, name, source)
    except HTTPException as exc:
        return form_error(request, exc.detail, "#tag-form-error")
    return _render_tags(request, session, customer_id, current_user)


@router.delete("/fragments/customers/{customer_id}/tags/{tag_id}", response_class=HTMLResponse)
def remove_tag_fragment(
    request: Request,
    customer_id: int,
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return _redirect_to_login()
    if current_user.role != UserRole.ADMIN:
        return form_error(request, "Solo un administrador puede quitar tags.", "#tag-form-error")

    try:
        customer_tag_service.remove_tag(session, customer_id, tag_id)
    except HTTPException as exc:
        return form_error(request, exc.detail, "#tag-form-error")
    return _render_tags(request, session, customer_id, current_user)


# --- Tareas del cliente -----------------------------------------------------


def _optional_int(value: str) -> Optional[int]:
    return int(value) if value.strip() else None


@router.post("/fragments/customers/{customer_id}/tasks", response_class=HTMLResponse)
def create_customer_task_fragment(
    request: Request,
    customer_id: int,
    title: str = Form(""),
    description: str = Form(""),
    priority: str = Form(TaskPriority.MEDIUM.value),
    due_date: str = Form(""),
    deal_id: str = Form(""),
    assigned_to: str = Form(""),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Crea una tarea desde el formulario manual o desde una sugerencia IA (un clic)."""
    if current_user is None:
        return _redirect_to_login()

    try:
        data = TaskCreate(
            title=title.strip(),
            description=description.strip() or None,
            priority=priority,
            due_date=date.fromisoformat(due_date) if due_date.strip() else None,
            customer_id=customer_id,
            deal_id=_optional_int(deal_id),
            assigned_to=_optional_int(assigned_to),
        )
        task_service.create_task(session, data, current_user)
    except (ValueError, ValidationError):
        return form_error(
            request,
            "Revise los datos: el título es obligatorio y la fecha debe ser válida.",
            "#task-form-error",
        )
    except HTTPException as exc:
        return form_error(request, exc.detail, "#task-form-error")

    return templates.TemplateResponse(
        request, "partials/customer_tasks.html", tasks_context(session, customer_id, current_user)
    )
