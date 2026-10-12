from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_admin
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.common import error_responses
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get(
    "/",
    response_model=List[TaskRead],
    summary="Listar tareas",
    responses=error_responses(401, 404),
)
def list_tasks(
    customer_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    mine: bool = False,
    overdue: bool = False,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """`mine=true` filtra por el usuario autenticado; `overdue=true` deja solo pendientes vencidas."""
    return task_service.list_tasks(
        session,
        customer_id=customer_id,
        assigned_to=current_user.id if mine else assigned_to,
        task_status=status,
        priority=priority,
        overdue=overdue,
    )


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Obtener una tarea",
    responses=error_responses(401, 404),
)
def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Datos de una tarea."""
    return task_service.get_task(session, task_id)


@router.post(
    "/",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear tarea",
    responses=error_responses(401, 403, 404),
)
def create_task(
    data: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Crea una tarea, asignada por defecto al usuario autenticado.

    Asignarla a otro usuario requiere `admin` (**403**). El deal, si se indica, debe ser del
    mismo cliente (**422**)."""
    return task_service.create_task(session, data, current_user)


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    summary="Actualizar tarea (parcial)",
    responses=error_responses(401, 403, 404),
)
def update_task(
    task_id: int,
    data: TaskUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Actualiza solo los campos enviados (ej. `{"status": "DONE"}`). Reasignar requiere `admin`."""
    return task_service.update_task(session, task_id, data, current_user)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar tarea (admin)",
    responses=error_responses(401, 403, 404),
)
def delete_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    """Elimina una tarea. Solo `admin`."""
    task_service.delete_task(session, task_id)
