from typing import List

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.interaction import Interaction
from app.models.interaction_type import InteractionType
from app.models.user import User
from app.repositories import interaction_repository
from app.schemas.interaction import InteractionCreate
from app.services import customer_service


def list_interactions(session: Session, customer_id: int) -> List[Interaction]:
    customer_service.get_customer(session, customer_id)
    return interaction_repository.get_by_customer(session, customer_id)


def create_interaction(
    session: Session,
    customer_id: int,
    data: InteractionCreate,
    current_user: User,
) -> Interaction:
    customer_service.get_customer(session, customer_id)

    interaction_type = session.get(InteractionType, data.interaction_type_id)
    if interaction_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de interacción no encontrado",
        )

    interaction = Interaction(
        notes=data.notes,
        customer_id=customer_id,
        interaction_type_id=data.interaction_type_id,
        user_id=current_user.id,
    )
    return interaction_repository.create(session, interaction)
