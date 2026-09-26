from sqlmodel import SQLModel, Session, create_engine, text

from app.core.config import settings

engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    from app import models  # noqa: F401 - registra los modelos en SQLModel.metadata

    # create_all es idempotente (checkfirst): solo emite CREATE TABLE para las
    # tablas que aún no existen (ej. `deals`, Fase 5) y nunca toca las existentes
    # ni sus datos.
    SQLModel.metadata.create_all(engine)

    # No hay herramienta de migraciones en el MVP; para columnas nuevas en tablas
    # ya existentes (create_all no las agrega) alcanza con un ALTER idempotente.
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE ai_summaries ADD COLUMN IF NOT EXISTS sentiment VARCHAR(20)")
        )


def get_session():
    with Session(engine) as session:
        yield session
