from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.customer_tag import TagSource


class CustomerTagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    source: TagSource = TagSource.MANUAL


class CustomerTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source: TagSource
    created_at: datetime
    customer_id: int
