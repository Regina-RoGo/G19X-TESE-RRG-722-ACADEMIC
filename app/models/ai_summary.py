import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.customer import Customer


class Sentiment(str, enum.Enum):
    POSITIVO = "POSITIVO"
    NEUTRAL = "NEUTRAL"
    NEGATIVO = "NEGATIVO"


class AISummary(SQLModel, table=True):
    __tablename__ = "ai_summaries"

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    sentiment: Optional[str] = Field(default=None, max_length=20)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    customer_id: int = Field(foreign_key="customers.id")

    customer: "Customer" = Relationship(back_populates="ai_summaries")
