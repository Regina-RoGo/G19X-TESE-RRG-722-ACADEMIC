from typing import List, Optional

from sqlmodel import Session, func, or_, select

from app.models.customer import Customer


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


def search(session: Session, query: str) -> List[Customer]:
    pattern = f"%{query}%"
    statement = select(Customer).where(
        or_(Customer.name.ilike(pattern), Customer.email.ilike(pattern))
    ).order_by(Customer.name)
    return list(session.exec(statement).all())


def update(session: Session, customer: Customer) -> Customer:
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def delete(session: Session, customer: Customer) -> None:
    session.delete(customer)
    session.commit()
