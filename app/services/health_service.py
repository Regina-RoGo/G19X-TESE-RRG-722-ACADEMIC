from sqlmodel import Session

from app.repositories import health_repository


def get_health_status(session: Session) -> dict:
    try:
        health_repository.check_database_connection(session)
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {"status": "ok", "database": db_status}
