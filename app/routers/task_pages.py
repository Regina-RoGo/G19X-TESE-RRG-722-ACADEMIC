"""Pantalla "Mis tareas" y cambio de estado de tareas vía HTMX (Fase 6)."""
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user_optional
from app.core.templating import templates
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.repositories import user_repository
from app.schemas.task import TaskUpdate
from app.services import task_service

router = APIRouter(tags=["pages"])

# Filtro de estado de la vista: "OVERDUE" = pendientes con vencimiento pasado.
STATUS_FILTERS = {
    "PENDING": "Pendientes",
    "OVERDUE": "Vencidas",
    "DONE": "Completadas",
    "": "Todas",
}


def _tasks_table_context(
    session: Session,
    current_user: User,
    task_status: str,
    priority: str,
    assigned: str,
) -> dict:
    # "me" (por defecto) = usuario autenticado; "" = todos; un id = ese usuario.
    if assigned == "me":
        assigned_to = current_user.id
    elif assigned.isdigit():
        assigned_to = int(assigned)
    else:
        assigned_to = None

    tasks = task_service.list_tasks(
        session,
        assigned_to=assigned_to,
        task_status=TaskStatus(task_status) if task_status in TaskStatus.__members__ else None,
        priority=TaskPriority(priority) if priority in TaskPriority.__members__ else None,
        overdue=task_status == "OVERDUE",
    )
    return {"tasks": tasks, "show_customer": True}


@router.get("/tasks", response_class=HTMLResponse)
def my_tasks_page(
    request: Request,
    status_filter: str = "PENDING",
    priority: str = "",
    assigned: str = "me",
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request,
        "tasks.html",
        {
            **_tasks_table_context(session, current_user, status_filter, priority, assigned),
            "status_filters": STATUS_FILTERS,
            "selected_status": status_filter,
            "selected_priority": priority,
            "selected_assigned": assigned,
            "users": user_repository.get_all(session),
            "current_user": current_user,
        },
    )


@router.get("/fragments/tasks/table", response_class=HTMLResponse)
def tasks_table_fragment(
    request: Request,
    status_filter: str = "PENDING",
    priority: str = "",
    assigned: str = "me",
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request,
        "partials/tasks_table.html",
        _tasks_table_context(session, current_user, status_filter, priority, assigned),
    )


@router.post("/fragments/tasks/{task_id}/status", response_class=HTMLResponse)
def change_task_status_fragment(
    request: Request,
    task_id: int,
    new_status: TaskStatus = Form(..., alias="status"),
    show_customer: bool = Form(False),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Marca una tarea como completada (o la reabre) y devuelve solo su fila."""
    if current_user is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        task = task_service.update_task(
            session, task_id, TaskUpdate(status=new_status), current_user
        )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request,
            "partials/task_row_error.html",
            {"error": exc.detail, "show_customer": show_customer},
        )

    return templates.TemplateResponse(
        request, "partials/task_row.html", {"task": task, "show_customer": show_customer}
    )
