import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.customer import Customer


class TagSource(str, enum.Enum):
    IA = "IA"
    MANUAL = "MANUAL"


class CustomerTag(SQLModel, table=True):
    """Etiqueta de segmentación aplicada a un cliente (sugerida por IA o manual)."""

    __tablename__ = "customer_tags"
    __table_args__ = (UniqueConstraint("customer_id", "name", name="uq_customer_tags_customer_name"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    # Normalizado (minúsculas, espacios simples) para que el filtro agrupe bien.
    name: str = Field(max_length=40, index=True)
    source: TagSource = Field(
        default=TagSource.MANUAL,
        sa_type=SAEnum(TagSource, native_enum=False, length=10),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    customer_id: int = Field(foreign_key="customers.id", index=True)

    customer: "Customer" = Relationship(back_populates="tags")
