from datetime import date, datetime
from typing import Dict, List

from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.models.interaction import Interaction


def create(session: Session, interaction: Interaction) -> Interaction:
    session.add(interaction)
    session.commit()
    session.refresh(interaction)
    return interaction


def get_by_customer(session: Session, customer_id: int) -> List[Interaction]:
    statement = (
        select(Interaction)
        .where(Interaction.customer_id == customer_id)
        .order_by(Interaction.occurred_at.desc())
    )
    return list(session.exec(statement).all())


def count(session: Session) -> int:
    return session.exec(select(func.count()).select_from(Interaction)).one()


def count_by_customer(session: Session, customer_id: int) -> int:
    statement = (
        select(func.count())
        .select_from(Interaction)
        .where(Interaction.customer_id == customer_id)
    )
    return session.exec(statement).one()


def get_recent(session: Session, limit: int = 5) -> List[Interaction]:
    # El dashboard muestra cliente y tipo de cada interacción: se cargan agrupados.
    statement = (
        select(Interaction)
        .options(selectinload(Interaction.customer), selectinload(Interaction.interaction_type))
        .order_by(Interaction.occurred_at.desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def count_by_day(session: Session, since: datetime) -> Dict[date, int]:
    day = func.date(Interaction.occurred_at)
    statement = (
        select(day, func.count())
        .where(Interaction.occurred_at >= since)
        .group_by(day)
    )
    return dict(session.exec(statement).all())
