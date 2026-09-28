from datetime import date, datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from app.models.customer_insight import ChurnRisk
from app.models.task import TaskPriority


class SuggestedTask(BaseModel):
    title: str
    priority: TaskPriority
    due_date: date


class CustomerInsightRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_score: int
    lead_score_justification: str
    churn_risk: ChurnRisk
    churn_justification: str
    suggested_tags: List[str]
    suggested_tasks: List[SuggestedTask]
    generated_at: datetime
    customer_id: int
