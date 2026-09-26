from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.interaction import Interaction


class InteractionType(SQLModel, table=True):
    __tablename__ = "interaction_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

    interactions: List["Interaction"] = Relationship(back_populates="interaction_type")
