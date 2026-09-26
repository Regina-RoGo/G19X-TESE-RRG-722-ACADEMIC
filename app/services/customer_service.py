import csv
import io
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.models.customer import Customer
from app.repositories import (
    ai_summary_repository,
    customer_repository,
    deal_repository,
    interaction_repository,
    sales_suggestion_repository,
)
from app.schemas.customer import CustomerCreate, CustomerUpdate


def list_customers(session: Session, search: Optional[str] = None) -> List[Customer]:
    if search:
        return customer_repository.search(session, search)
    return customer_repository.get_all(session)


def get_customer(session: Session, customer_id: int) -> Customer:
    customer = customer_repository.get_by_id(session, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )
    return customer


def create_customer(session: Session, data: CustomerCreate) -> Customer:
    customer = Customer(**data.model_dump())
    return customer_repository.create(session, customer)


def update_customer(session: Session, customer_id: int, data: CustomerUpdate) -> Customer:
    customer = get_customer(session, customer_id)
    for field, value in data.model_dump().items():
        setattr(customer, field, value)
    return customer_repository.update(session, customer)


def delete_customer(session: Session, customer_id: int) -> None:
    customer = get_customer(session, customer_id)

    # Un cliente con actividad no se borra: se conserva su historial comercial
    # en vez de borrar en cascada (y en vez de dejar que la FK termine en un 500).
    related = [
        (deal_repository.count_by_customer(session, customer_id), "deal", "deals"),
        (interaction_repository.count_by_customer(session, customer_id), "interacción", "interacciones"),
        (ai_summary_repository.count_by_customer(session, customer_id), "resumen IA", "resúmenes IA"),
        (
            sales_suggestion_repository.count_by_customer(session, customer_id),
            "sugerencia de venta IA",
            "sugerencias de venta IA",
        ),
    ]
    blockers = [f"{n} {singular if n == 1 else plural}" for n, singular, plural in related if n]
    if blockers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede eliminar el cliente '{customer.name}' porque tiene "
                f"registros asociados: {', '.join(blockers)}. "
                "Para conservar el historial comercial, solo se pueden eliminar clientes sin actividad."
            ),
        )

    try:
        customer_repository.delete(session, customer)
    except IntegrityError:
        # Carrera: se asoció un registro entre la verificación y el borrado.
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede eliminar el cliente '{customer.name}' porque tiene registros asociados.",
        )


def export_customers_csv(session: Session) -> str:
    customers = customer_repository.get_all(session)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["ID", "Nombre", "Email", "Teléfono", "Fecha de Registro"])
    for customer in customers:
        writer.writerow(
            [
                customer.id,
                customer.name,
                customer.email or "",
                customer.phone or "",
                customer.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )

    return "﻿" + buffer.getvalue()
