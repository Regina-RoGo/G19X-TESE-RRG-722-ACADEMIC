from typing import List, Optional

from sqlmodel import Session, select

from app.models.user import User


def get_by_id(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)


def get_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()


def get_all(session: Session) -> List[User]:
    return list(session.exec(select(User).order_by(User.full_name)).all())
