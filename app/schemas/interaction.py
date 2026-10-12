from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InteractionCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "notes": "Demo del sistema; piden propuesta con integración a facturación.",
                    "interaction_type_id": 3,
                }
            ]
        }
    )

    notes: str
    interaction_type_id: int


class InteractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notes: str
    occurred_at: datetime
    customer_id: int
    interaction_type_id: int
    user_id: int
