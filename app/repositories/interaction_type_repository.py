from typing import List

from sqlmodel import Session, select

from app.models.interaction_type import InteractionType


def get_all(session: Session) -> List[InteractionType]:
    return list(session.exec(select(InteractionType).order_by(InteractionType.name)).all())
