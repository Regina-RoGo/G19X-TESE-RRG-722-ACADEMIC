from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.deal import DealStage


class DealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    value: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    stage: DealStage = DealStage.PROSPECT
    probability: int = Field(default=0, ge=0, le=100)
    customer_id: int


class DealUpdate(BaseModel):
    """Actualización parcial: solo se modifican los campos enviados."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    value: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    stage: Optional[DealStage] = None
    probability: Optional[int] = Field(default=None, ge=0, le=100)


class DealStageUpdate(BaseModel):
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
