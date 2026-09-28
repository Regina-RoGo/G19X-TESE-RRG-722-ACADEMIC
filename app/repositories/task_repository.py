from datetime import date
from typing import List, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.models.task import Task, TaskPriority, TaskStatus


def create(session: Session, task: Task) -> Task:
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_by_id(session: Session, task_id: int) -> Optional[Task]:
    return session.get(Task, task_id)


def get_all(
    session: Session,
    customer_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    overdue_before: Optional[date] = None,
) -> List[Task]:
    # Las vistas muestran cliente y responsable de cada tarea: se cargan en
    # consultas agrupadas en vez de una por tarea.
    statement = select(Task).options(selectinload(Task.customer), selectinload(Task.assignee))
    if customer_id is not None:
        statement = statement.where(Task.customer_id == customer_id)
    if assigned_to is not None:
        statement = statement.where(Task.assigned_to == assigned_to)
    if status is not None:
        statement = statement.where(Task.status == status)
    if priority is not None:
        statement = statement.where(Task.priority == priority)
    if overdue_before is not None:
        statement = statement.where(
            Task.status == TaskStatus.PENDING, Task.due_date < overdue_before
        )
    # Pendientes primero, luego por vencimiento (sin fecha al final).
    statement = statement.order_by(
        Task.status.desc(), Task.due_date.asc().nulls_last(), Task.created_at.desc()
    )
    return list(session.exec(statement).all())


def count_by_customer(session: Session, customer_id: int) -> int:
    statement = select(func.count()).select_from(Task).where(Task.customer_id == customer_id)
    return session.exec(statement).one()


def update(session: Session, task: Task) -> Task:
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete(session: Session, task: Task) -> None:
    session.delete(task)
    session.commit()
