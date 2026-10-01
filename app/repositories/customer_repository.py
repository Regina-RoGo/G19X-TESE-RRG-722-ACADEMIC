from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, or_, select

from app.models.customer import Customer
from app.models.customer_insight import ChurnRisk, CustomerInsight
from app.models.customer_tag import CustomerTag
from app.models.deal import Deal, DealStage
from app.models.interaction import Interaction
from app.repositories import customer_insight_repository


def create(session: Session, customer: Customer) -> Customer:
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def get_by_id(session: Session, customer_id: int) -> Optional[Customer]:
    return session.get(Customer, customer_id)


def get_all(session: Session) -> List[Customer]:
    return list(session.exec(select(Customer).order_by(Customer.name)).all())


def count(session: Session) -> int:
    return session.exec(select(func.count()).select_from(Customer)).one()


def count_active(session: Session, since: datetime) -> int:
    """Clientes con alguna interacción desde `since` o con al menos un deal abierto."""
    recent_contact = select(Interaction.customer_id).where(Interaction.occurred_at >= since)
    open_deal = select(Deal.customer_id).where(
        Deal.stage.not_in([DealStage.CLOSED_WON, DealStage.CLOSED_LOST])
    )
    statement = (
        select(func.count())
        .select_from(Customer)
        .where(or_(Customer.id.in_(recent_contact), Customer.id.in_(open_deal)))
    )
    return session.exec(statement).one()


def churn_distribution(session: Session) -> Dict[ChurnRisk, int]:
    """Clientes por nivel de churn según su análisis más reciente."""
    statement = (
        select(CustomerInsight.churn_risk, func.count())
        .where(CustomerInsight.id.in_(customer_insight_repository.latest_ids_subquery()))
        .group_by(CustomerInsight.churn_risk)
    )
    return dict(session.exec(statement).all())


def get_recent(session: Session, limit: int = 5) -> List[Customer]:
    statement = select(Customer).order_by(Customer.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())


def filter_customers(
    session: Session,
    query: Optional[str] = None,
    tag: Optional[str] = None,
    churn_risk: Optional[ChurnRisk] = None,
) -> List[Customer]:
    # La lista muestra los tags de cada cliente: se cargan en una sola consulta extra.
    statement = select(Customer).options(selectinload(Customer.tags))
    if query:
        pattern = f"%{query}%"
        statement = statement.where(
            or_(Customer.name.ilike(pattern), Customer.email.ilike(pattern))
        )
    if tag:
        statement = statement.where(
            Customer.id.in_(select(CustomerTag.customer_id).where(CustomerTag.name == tag))
        )
    if churn_risk is not None:
        # Solo cuenta el análisis más reciente de cada cliente.
        latest = customer_insight_repository.latest_ids_subquery()
        statement = statement.join(
            CustomerInsight, CustomerInsight.customer_id == Customer.id
        ).where(CustomerInsight.id.in_(latest), CustomerInsight.churn_risk == churn_risk)
    return list(session.exec(statement.order_by(Customer.name)).all())


def update(session: Session, customer: Customer) -> Customer:
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def delete(session: Session, customer: Customer) -> None:
    session.delete(customer)
    session.commit()
