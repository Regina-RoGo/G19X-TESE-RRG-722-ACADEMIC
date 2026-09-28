from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User, UserRole
from app.repositories import task_repository, user_repository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import customer_service, deal_service

PRIORITY_LABELS = {
    TaskPriority.HIGH: "Alta",
    TaskPriority.MEDIUM: "Media",
    TaskPriority.LOW: "Baja",
}

# Campos que admiten null explícito para "vaciarlos"; en el resto un null se ignora.
NULLABLE_FIELDS = {"description", "due_date", "deal_id"}


def _validate_deal(session: Session, deal_id: int, customer_id: int) -> None:
    deal = deal_service.get_deal(session, deal_id)
    if deal.customer_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El deal indicado no pertenece al cliente de la tarea.",
        )


def _validate_assignee(session: Session, user_id: int) -> None:
    if user_repository.get_by_id(session, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario asignado no encontrado",
        )


def _forbid_reassign(current_user: User) -> None:
    # RBAC del roadmap: asignar/reasignar tareas a otra persona es solo de admin.
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede asignar tareas a otro usuario.",
        )


def list_tasks(
    session: Session,
    customer_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    task_status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    overdue: bool = False,
) -> List[Task]:
    if customer_id is not None:
        customer_service.get_customer(session, customer_id)
    return task_repository.get_all(
        session,
        customer_id=customer_id,
        assigned_to=assigned_to,
        status=task_status,
        priority=priority,
        overdue_before=date.today() if overdue else None,
    )


def get_task(session: Session, task_id: int) -> Task:
    task = task_repository.get_by_id(session, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada",
        )
    return task


def create_task(session: Session, data: TaskCreate, current_user: User) -> Task:
    customer_service.get_customer(session, data.customer_id)
    if data.deal_id is not None:
        _validate_deal(session, data.deal_id, data.customer_id)

    assigned_to = data.assigned_to if data.assigned_to is not None else current_user.id
    if assigned_to != current_user.id:
        _forbid_reassign(current_user)
        _validate_assignee(session, assigned_to)

    task = Task(**data.model_dump(exclude={"assigned_to"}), assigned_to=assigned_to)
    return task_repository.create(session, task)


def update_task(session: Session, task_id: int, data: TaskUpdate, current_user: User) -> Task:
    task = get_task(session, task_id)
    changes = {
        field: value
        for field, value in data.model_dump(exclude_unset=True).items()
        if value is not None or field in NULLABLE_FIELDS
    }

    if changes.get("deal_id") is not None:
        _validate_deal(session, changes["deal_id"], task.customer_id)
    if "assigned_to" in changes and changes["assigned_to"] != task.assigned_to:
        _forbid_reassign(current_user)
        _validate_assignee(session, changes["assigned_to"])

    for field, value in changes.items():
        setattr(task, field, value)
    return task_repository.update(session, task)


def delete_task(session: Session, task_id: int) -> None:
    task = get_task(session, task_id)
    task_repository.delete(session, task)
