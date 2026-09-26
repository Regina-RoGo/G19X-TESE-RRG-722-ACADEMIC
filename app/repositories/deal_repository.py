from typing import List, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.models.deal import Deal, DealStage


def create(session: Session, deal: Deal) -> Deal:
    session.add(deal)
    session.commit()
    session.refresh(deal)
    return deal


def get_by_id(session: Session, deal_id: int) -> Optional[Deal]:
    return session.get(Deal, deal_id)


def get_all(
    session: Session,
    stage: Optional[DealStage] = None,
    customer_id: Optional[int] = None,
) -> List[Deal]:
    # El tablero muestra el nombre del cliente en cada tarjeta: se carga en una
    # sola consulta extra en vez de una por deal.
    statement = select(Deal).options(selectinload(Deal.customer))
    if stage is not None:
        statement = statement.where(Deal.stage == stage)
    if customer_id is not None:
        statement = statement.where(Deal.customer_id == customer_id)
    return list(session.exec(statement.order_by(Deal.updated_at.desc())).all())


def get_by_customer(session: Session, customer_id: int) -> List[Deal]:
    statement = (
        select(Deal)
        .where(Deal.customer_id == customer_id)
        .order_by(Deal.updated_at.desc())
    )
    return list(session.exec(statement).all())


def count(session: Session) -> int:
    return session.exec(select(func.count()).select_from(Deal)).one()


def count_by_customer(session: Session, customer_id: int) -> int:
    statement = select(func.count()).select_from(Deal).where(Deal.customer_id == customer_id)
    return session.exec(statement).one()


def update(session: Session, deal: Deal) -> Deal:
    session.add(deal)
    session.commit()
    session.refresh(deal)
    return deal


def delete(session: Session, deal: Deal) -> None:
    session.delete(deal)
    session.commit()
