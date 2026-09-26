from typing import Optional

from sqlmodel import Session, select

from app.models.user import User


def get_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()
