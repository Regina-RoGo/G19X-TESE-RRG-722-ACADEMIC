from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.customer import Customer
    from app.models.interaction_type import InteractionType


class Interaction(SQLModel, table=True):
    __tablename__ = "interactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    notes: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)

    customer_id: int = Field(foreign_key="customers.id")
    interaction_type_id: int = Field(foreign_key="interaction_types.id")
    user_id: int = Field(foreign_key="users.id")

    customer: "Customer" = Relationship(back_populates="interactions")
    interaction_type: "InteractionType" = Relationship(back_populates="interactions")
    user: "User" = Relationship(back_populates="interactions")
