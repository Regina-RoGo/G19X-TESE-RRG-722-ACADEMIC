from typing import Optional

from sqlmodel import Session, func, select

from app.models.sales_suggestion import SalesSuggestion


def create(session: Session, suggestion: SalesSuggestion) -> SalesSuggestion:
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)
    return suggestion


def get_latest_by_customer(session: Session, customer_id: int) -> Optional[SalesSuggestion]:
    statement = (
        select(SalesSuggestion)
        .where(SalesSuggestion.customer_id == customer_id)
        .order_by(SalesSuggestion.generated_at.desc())
    )
    return session.exec(statement).first()


def count_by_customer(session: Session, customer_id: int) -> int:
    statement = (
        select(func.count())
        .select_from(SalesSuggestion)
        .where(SalesSuggestion.customer_id == customer_id)
    )
    return session.exec(statement).one()
