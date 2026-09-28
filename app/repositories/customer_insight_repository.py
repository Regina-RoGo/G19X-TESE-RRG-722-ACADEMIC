from typing import Dict, List, Optional

from sqlmodel import Session, func, select

from app.models.customer_insight import CustomerInsight


def create(session: Session, insight: CustomerInsight) -> CustomerInsight:
    session.add(insight)
    session.commit()
    session.refresh(insight)
    return insight


def get_latest_by_customer(session: Session, customer_id: int) -> Optional[CustomerInsight]:
    statement = (
        select(CustomerInsight)
        .where(CustomerInsight.customer_id == customer_id)
        .order_by(CustomerInsight.id.desc())
    )
    return session.exec(statement).first()


def latest_ids_subquery():
    """IDs del análisis más reciente de cada cliente (el id crece con cada generación)."""
    return select(func.max(CustomerInsight.id)).group_by(CustomerInsight.customer_id)


def get_latest_by_customers(session: Session, customer_ids: List[int]) -> Dict[int, CustomerInsight]:
    if not customer_ids:
        return {}
    statement = select(CustomerInsight).where(
        CustomerInsight.id.in_(latest_ids_subquery()),
        CustomerInsight.customer_id.in_(customer_ids),
    )
    return {insight.customer_id: insight for insight in session.exec(statement).all()}


def count_by_customer(session: Session, customer_id: int) -> int:
    statement = (
        select(func.count())
        .select_from(CustomerInsight)
        .where(CustomerInsight.customer_id == customer_id)
    )
    return session.exec(statement).one()
