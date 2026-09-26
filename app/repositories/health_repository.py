from sqlmodel import Session, text


def check_database_connection(session: Session) -> bool:
    session.exec(text("SELECT 1"))
    return True
