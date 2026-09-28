from typing import List, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, or_, select

from app.models.customer import Customer
from app.models.customer_insight import ChurnRisk, CustomerInsight
from app.models.customer_tag import CustomerTag
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
