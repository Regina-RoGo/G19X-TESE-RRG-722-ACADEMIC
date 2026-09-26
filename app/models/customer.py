from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.interaction import Interaction
    from app.models.ai_summary import AISummary
    from app.models.deal import Deal
    from app.models.sales_suggestion import SalesSuggestion


class Customer(SQLModel, table=True):
    __tablename__ = "customers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = Field(default=None, index=True)
    phone: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    interactions: List["Interaction"] = Relationship(back_populates="customer")
    ai_summaries: List["AISummary"] = Relationship(back_populates="customer")
    deals: List["Deal"] = Relationship(back_populates="customer")
    sales_suggestions: List["SalesSuggestion"] = Relationship(back_populates="customer")
