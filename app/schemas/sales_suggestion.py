from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class SalesSuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    next_steps: List[str]
    closing_strategy: str
    generated_at: datetime
    customer_id: int
