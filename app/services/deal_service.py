from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.deal import Deal, DealStage
from app.repositories import deal_repository
from app.schemas.deal import DealCreate, DealUpdate
from app.services import customer_service

# Orden y nombre visible de las columnas del tablero.
STAGE_LABELS = {
    DealStage.PROSPECT: "Prospecto",
    DealStage.CONTACTED: "Contactado",
    DealStage.PROPOSAL_SENT: "Propuesta Enviada",
    DealStage.CLOSED_WON: "Ganado",
    DealStage.CLOSED_LOST: "Perdido",
}

# Una etapa cerrada fija la probabilidad: ganado = 100 %, perdido = 0 %.
CLOSED_STAGE_PROBABILITY = {
    DealStage.CLOSED_WON: 100,
    DealStage.CLOSED_LOST: 0,
}

# Al reabrir un deal cerrado, la probabilidad vuelve al valor base de la etapa.
OPEN_STAGE_DEFAULT_PROBABILITY = {
    DealStage.PROSPECT: 10,
    DealStage.CONTACTED: 30,
    DealStage.PROPOSAL_SENT: 60,
}


def _apply_stage_rules(
    deal: Deal,
    previous_stage: Optional[DealStage] = None,
    probability_given: bool = False,
) -> None:
    if deal.stage in CLOSED_STAGE_PROBABILITY:
        deal.probability = CLOSED_STAGE_PROBABILITY[deal.stage]
    elif previous_stage in CLOSED_STAGE_PROBABILITY and not probability_given:
        deal.probability = OPEN_STAGE_DEFAULT_PROBABILITY[deal.stage]


def list_deals(
    session: Session,
    stage: Optional[DealStage] = None,
    customer_id: Optional[int] = None,
) -> List[Deal]:
    if customer_id is not None:
        customer_service.get_customer(session, customer_id)
    return deal_repository.get_all(session, stage=stage, customer_id=customer_id)


def get_pipeline(session: Session) -> List[dict]:
    """Deals agrupados por etapa, en el orden de las columnas del tablero."""
    deals = deal_repository.get_all(session)
    columns = []
    for stage, label in STAGE_LABELS.items():
        stage_deals = [deal for deal in deals if deal.stage == stage]
        columns.append(
            {
                "stage": stage,
                "label": label,
                "deals": stage_deals,
                "total": sum((deal.value for deal in stage_deals), Decimal("0")),
            }
        )
    return columns


def get_deal(session: Session, deal_id: int) -> Deal:
    deal = deal_repository.get_by_id(session, deal_id)
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal no encontrado",
        )
    return deal


def create_deal(session: Session, data: DealCreate) -> Deal:
    customer_service.get_customer(session, data.customer_id)

    now = datetime.utcnow()
    deal = Deal(**data.model_dump(), created_at=now, updated_at=now)
    _apply_stage_rules(deal)
    return deal_repository.create(session, deal)


def update_deal(session: Session, deal_id: int, data: DealUpdate) -> Deal:
    deal = get_deal(session, deal_id)
    previous_stage = deal.stage
    changes = {
        # null explícito en un campo obligatorio: se ignora en vez de romper el NOT NULL
        field: value
        for field, value in data.model_dump(exclude_unset=True).items()
        if value is not None
    }
    for field, value in changes.items():
        setattr(deal, field, value)
    _apply_stage_rules(deal, previous_stage, probability_given="probability" in changes)
    deal.updated_at = datetime.utcnow()
    return deal_repository.update(session, deal)


def change_stage(session: Session, deal_id: int, stage: DealStage) -> Deal:
    deal = get_deal(session, deal_id)
    if deal.stage == stage:
        return deal
    previous_stage = deal.stage
    deal.stage = stage
    _apply_stage_rules(deal, previous_stage)
    deal.updated_at = datetime.utcnow()
    return deal_repository.update(session, deal)


def delete_deal(session: Session, deal_id: int) -> None:
    deal = get_deal(session, deal_id)
    deal_repository.delete(session, deal)
