import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.deal import Deal
    from app.models.user import User


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    DONE = "DONE"


class TaskPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_type=SAEnum(TaskStatus, native_enum=False, length=10),
        index=True,
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        sa_type=SAEnum(TaskPriority, native_enum=False, length=10),
    )
    due_date: Optional[date] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    customer_id: int = Field(foreign_key="customers.id", index=True)
    # Borrar un deal no borra sus tareas: quedan asociadas solo al cliente.
    deal_id: Optional[int] = Field(
        default=None, foreign_key="deals.id", index=True, ondelete="SET NULL"
    )
    assigned_to: int = Field(foreign_key="users.id", index=True)

    customer: "Customer" = Relationship(back_populates="tasks")
    deal: Optional["Deal"] = Relationship()
    assignee: "User" = Relationship()
