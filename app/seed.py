"""Script de inicialización de datos del MVP.

Pobla el catálogo de interaction_types y crea el usuario admin base.
Es idempotente: se puede ejecutar varias veces sin duplicar datos.

Uso local:      python -m app.seed
Uso en Docker:  docker compose exec app python -m app.seed
"""

from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine, init_db
from app.core.security import hash_password
from app.models import InteractionType, User, UserRole

INTERACTION_TYPES = ["Llamada", "Correo", "Reunión", "Ticket"]


def seed_interaction_types(session: Session) -> None:
    for name in INTERACTION_TYPES:
        existing = session.exec(
            select(InteractionType).where(InteractionType.name == name)
        ).first()
        if not existing:
            session.add(InteractionType(name=name))
    session.commit()


def seed_admin_user(session: Session) -> None:
    existing = session.exec(
        select(User).where(User.email == settings.admin_email)
    ).first()
    if existing:
        return

    admin = User(
        full_name=settings.admin_full_name,
        email=settings.admin_email,
        hashed_password=hash_password(settings.admin_password),
        role=UserRole.ADMIN,
    )
    session.add(admin)
    session.commit()


def run_seed() -> None:
    init_db()
    with Session(engine) as session:
        seed_interaction_types(session)
        seed_admin_user(session)


if __name__ == "__main__":
    run_seed()
    print("Seed completado: interaction_types poblado y usuario admin listo.")
