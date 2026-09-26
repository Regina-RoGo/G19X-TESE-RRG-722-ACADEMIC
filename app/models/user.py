import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.interaction import Interaction


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    COMERCIAL = "comercial"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.COMERCIAL)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    interactions: List["Interaction"] = Relationship(back_populates="user")
