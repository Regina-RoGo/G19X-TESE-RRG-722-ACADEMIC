from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None
    customer_id: int
    deal_id: Optional[int] = None
    # Si se omite, la tarea queda asignada al usuario autenticado.
    assigned_to: Optional[int] = None


class TaskUpdate(BaseModel):
    """Actualización parcial: solo se modifican los campos enviados."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    deal_id: Optional[int] = None
    assigned_to: Optional[int] = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date]
    created_at: datetime
    customer_id: int
    deal_id: Optional[int]
    assigned_to: int
