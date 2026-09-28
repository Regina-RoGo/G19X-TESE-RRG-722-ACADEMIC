import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.customer import Customer


class ChurnRisk(str, enum.Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


class CustomerInsight(SQLModel, table=True):
    """Analítica predictiva de un cliente generada por IA (una fila por cálculo)."""

    __tablename__ = "customer_insights"

    id: Optional[int] = Field(default=None, primary_key=True)
    lead_score: int  # 0–100
    lead_score_justification: str
    # VARCHAR en vez de ENUM nativo (mismo criterio que deals.stage).
    churn_risk: ChurnRisk = Field(
        sa_type=SAEnum(ChurnRisk, native_enum=False, length=10),
        index=True,
    )
    churn_justification: str
    suggested_tags: List[str] = Field(default_factory=list, sa_type=JSON)
    # Tareas propuestas por la IA: [{"title", "priority", "due_date"}]. No se crean
    # solas; el usuario decide cuáles convertir en tareas reales.
    suggested_tasks: List[dict] = Field(default_factory=list, sa_type=JSON)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    customer_id: int = Field(foreign_key="customers.id", index=True)

    customer: "Customer" = Relationship(back_populates="insights")
