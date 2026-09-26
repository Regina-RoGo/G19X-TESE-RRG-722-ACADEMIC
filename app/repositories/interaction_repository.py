from typing import List

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
    statement = select(Interaction).order_by(Interaction.occurred_at.desc()).limit(limit)
    return list(session.exec(statement).all())
