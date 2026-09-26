from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
