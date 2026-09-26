from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.user import User, UserRole

COOKIE_NAME = "access_token"


def get_current_user(
    access_token: Optional[str] = Cookie(default=None, alias=COOKIE_NAME),
    session: Session = Depends(get_session),
) -> User:
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )

    try:
        payload = decode_access_token(access_token)
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    return user


def get_current_user_optional(
    access_token: Optional[str] = Cookie(default=None, alias=COOKIE_NAME),
    session: Session = Depends(get_session),
) -> Optional[User]:
    if access_token is None:
        return None

    try:
        payload = decode_access_token(access_token)
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None

    return session.get(User, user_id)


def require_role(*allowed_roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para esta acción",
            )
        return current_user

    return dependency


require_admin = require_role(UserRole.ADMIN)
