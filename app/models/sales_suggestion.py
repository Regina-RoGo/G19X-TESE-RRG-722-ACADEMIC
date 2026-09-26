from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.customer import Customer


class SalesSuggestion(SQLModel, table=True):
    __tablename__ = "sales_suggestions"

    id: Optional[int] = Field(default=None, primary_key=True)
    next_steps: List[str] = Field(default_factory=list, sa_type=JSON)
    closing_strategy: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    customer_id: int = Field(foreign_key="customers.id", index=True)

    customer: "Customer" = Relationship(back_populates="sales_suggestions")
