from datetime import timedelta

from sqlmodel import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories import user_repository


class InvalidCredentialsError(Exception):
    pass


def authenticate(session: Session, email: str, password: str) -> User:
    user = user_repository.get_by_email(session, email)
    if not user or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()
    return user


def create_user_token(user: User) -> str:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    return create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=expires_delta,
    )
