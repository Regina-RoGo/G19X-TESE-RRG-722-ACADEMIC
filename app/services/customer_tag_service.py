from typing import List

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.models.customer_tag import CustomerTag, TagSource
from app.repositories import customer_tag_repository
from app.services import customer_service

MAX_TAG_LENGTH = 40


def normalize_tag_name(name: str) -> str:
    """Minúsculas y espacios simples: 'Alto  Valor ' y 'alto valor' son el mismo tag."""
    return " ".join(name.strip().lower().split())[:MAX_TAG_LENGTH]


def list_tags(session: Session, customer_id: int) -> List[CustomerTag]:
    customer_service.get_customer(session, customer_id)
    return customer_tag_repository.get_by_customer(session, customer_id)


def list_tag_names(session: Session) -> List[str]:
    return customer_tag_repository.get_distinct_names(session)


def add_tag(session: Session, customer_id: int, name: str, source: TagSource) -> CustomerTag:
    customer_service.get_customer(session, customer_id)
    clean = normalize_tag_name(name)
    if not clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El nombre del tag no puede estar vacío.",
        )

    duplicate = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"El cliente ya tiene el tag '{clean}'.",
    )
    if customer_tag_repository.get_by_customer_and_name(session, customer_id, clean):
        raise duplicate
    try:
        return customer_tag_repository.create(
            session, CustomerTag(customer_id=customer_id, name=clean, source=source)
        )
    except IntegrityError:
        # Carrera: el mismo tag se aplicó entre la verificación y el insert.
        session.rollback()
        raise duplicate


def remove_tag(session: Session, customer_id: int, tag_id: int) -> None:
    tag = customer_tag_repository.get_by_id(session, tag_id)
    if tag is None or tag.customer_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag no encontrado para este cliente",
        )
    customer_tag_repository.delete_tag(session, tag)
