from decimal import Decimal
from typing import Dict, List, Optional

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


def stage_summary(session: Session) -> Dict[DealStage, dict]:
    """Cantidad, monto total y monto ponderado por probabilidad de cada etapa."""
    statement = select(
        Deal.stage,
        func.count(Deal.id),
        func.coalesce(func.sum(Deal.value), 0),
        func.coalesce(func.sum(Deal.value * Deal.probability / 100), 0),
    ).group_by(Deal.stage)
    return {
        stage: {"count": count, "total": Decimal(total), "weighted": Decimal(weighted)}
        for stage, count, total, weighted in session.exec(statement).all()
    }


def get_recent(session: Session, limit: int = 5) -> List[Deal]:
    statement = (
        select(Deal)
        .options(selectinload(Deal.customer))
        .order_by(Deal.updated_at.desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())

