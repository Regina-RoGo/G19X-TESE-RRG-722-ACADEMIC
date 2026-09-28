from typing import List, Optional

from sqlmodel import Session, delete, select

from app.models.customer_tag import CustomerTag


def create(session: Session, tag: CustomerTag) -> CustomerTag:
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


def get_by_id(session: Session, tag_id: int) -> Optional[CustomerTag]:
    return session.get(CustomerTag, tag_id)


def get_by_customer(session: Session, customer_id: int) -> List[CustomerTag]:
    statement = (
        select(CustomerTag)
        .where(CustomerTag.customer_id == customer_id)
        .order_by(CustomerTag.name)
    )
    return list(session.exec(statement).all())


def get_by_customer_and_name(session: Session, customer_id: int, name: str) -> Optional[CustomerTag]:
    statement = select(CustomerTag).where(
        CustomerTag.customer_id == customer_id, CustomerTag.name == name
    )
    return session.exec(statement).first()


def get_distinct_names(session: Session) -> List[str]:
    statement = select(CustomerTag.name).distinct().order_by(CustomerTag.name)
    return list(session.exec(statement).all())


def delete_tag(session: Session, tag: CustomerTag) -> None:
    session.delete(tag)
    session.commit()


def delete_by_customer(session: Session, customer_id: int) -> None:
    """Sin commit: se confirma junto con el borrado del cliente."""
    session.exec(delete(CustomerTag).where(CustomerTag.customer_id == customer_id))
