from typing import Optional

from sqlmodel import Session, func, select

from app.models.ai_summary import AISummary


def create(session: Session, ai_summary: AISummary) -> AISummary:
    session.add(ai_summary)
    session.commit()
    session.refresh(ai_summary)
    return ai_summary


def get_latest_by_customer(session: Session, customer_id: int) -> Optional[AISummary]:
    statement = (
        select(AISummary)
        .where(AISummary.customer_id == customer_id)
        .order_by(AISummary.generated_at.desc())
    )
    return session.exec(statement).first()


def count(session: Session) -> int:
    return session.exec(select(func.count()).select_from(AISummary)).one()


def count_by_customer(session: Session, customer_id: int) -> int:
    statement = (
        select(func.count())
        .select_from(AISummary)
        .where(AISummary.customer_id == customer_id)
    )
    return session.exec(statement).one()
