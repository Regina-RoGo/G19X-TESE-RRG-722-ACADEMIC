from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_admin
from app.models.deal import DealStage
from app.schemas.deal import DealCreate, DealRead, DealStageUpdate, DealUpdate
from app.services import deal_service

router = APIRouter(prefix="/api/deals", tags=["deals"])


@router.get("/", response_model=List[DealRead])
def list_deals(
    stage: Optional[DealStage] = None,
    customer_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return deal_service.list_deals(session, stage=stage, customer_id=customer_id)


@router.get("/{deal_id}", response_model=DealRead)
def get_deal(
    deal_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return deal_service.get_deal(session, deal_id)


@router.post("/", response_model=DealRead, status_code=status.HTTP_201_CREATED)
def create_deal(
    data: DealCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return deal_service.create_deal(session, data)


@router.patch("/{deal_id}", response_model=DealRead)
def update_deal(
    deal_id: int,
    data: DealUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return deal_service.update_deal(session, deal_id, data)


@router.patch("/{deal_id}/stage", response_model=DealRead)
def change_deal_stage(
    deal_id: int,
    data: DealStageUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return deal_service.change_stage(session, deal_id, data.stage)


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(
    deal_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    deal_service.delete_deal(session, deal_id)
