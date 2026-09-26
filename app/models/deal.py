import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.customer import Customer


class DealStage(str, enum.Enum):
    PROSPECT = "PROSPECT"
    CONTACTED = "CONTACTED"
    PROPOSAL_SENT = "PROPOSAL_SENT"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"


class Deal(SQLModel, table=True):
    __tablename__ = "deals"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    value: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    # VARCHAR en vez de ENUM nativo de Postgres: agregar/renombrar etapas no
    # requiere un ALTER TYPE (no hay herramienta de migraciones).
    stage: DealStage = Field(
        default=DealStage.PROSPECT,
        sa_type=SAEnum(DealStage, native_enum=False, length=20),
        index=True,
    )
    probability: int = Field(default=0)  # 0–100 (%)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )

    customer_id: int = Field(foreign_key="customers.id", index=True)

    customer: "Customer" = Relationship(back_populates="deals")
