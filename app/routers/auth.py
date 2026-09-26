from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.core.dependencies import COOKIE_NAME
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
) -> dict:
    try:
        user = auth_service.authenticate(session, email, password)
    except auth_service.InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    token = auth_service.create_user_token(user)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.app_env != "development",
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    return {"message": "Login exitoso", "role": user.role.value}
