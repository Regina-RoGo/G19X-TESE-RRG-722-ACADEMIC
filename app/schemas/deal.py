from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.deal import DealStage


class DealCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Ampliación a sucursales",
                    "value": "15000.00",
                    "stage": "PROPOSAL_SENT",
                    "probability": 60,
                    "customer_id": 5,
                }
            ]
        }
    )

    title: str = Field(min_length=1, max_length=200)
    value: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    stage: DealStage = DealStage.PROSPECT
    probability: int = Field(default=0, ge=0, le=100)
    customer_id: int


class DealUpdate(BaseModel):
    """Actualización parcial: solo se modifican los campos enviados."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"value": "18000.00", "probability": 70}]})

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    value: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    stage: Optional[DealStage] = None
    probability: Optional[int] = Field(default=None, ge=0, le=100)


class DealStageUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"stage": "CLOSED_WON"}]})

    stage: DealStage


class DealRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    value: Decimal
    stage: DealStage
    probability: int
    customer_id: int
    created_at: datetime
    updated_at: datetime
