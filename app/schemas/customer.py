from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None


CUSTOMER_EXAMPLE = {
    "name": "Mariana Ortega",
    "email": "mortega@logisticaandina.com",
    "phone": "+54 9 11 5555-1234",
    "company": "Logística Andina S.A.",
}


class CustomerCreate(CustomerBase):
    model_config = ConfigDict(json_schema_extra={"examples": [CUSTOMER_EXAMPLE]})


class CustomerUpdate(CustomerBase):
    model_config = ConfigDict(json_schema_extra={"examples": [CUSTOMER_EXAMPLE]})


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
