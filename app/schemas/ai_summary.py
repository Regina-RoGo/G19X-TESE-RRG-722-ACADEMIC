from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AISummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    sentiment: Optional[str] = None
    generated_at: datetime
    customer_id: int
