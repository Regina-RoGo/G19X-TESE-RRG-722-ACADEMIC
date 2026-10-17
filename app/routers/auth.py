from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.core.dependencies import COOKIE_NAME
from app.schemas.common import error_responses
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"message": "Login exitoso", "role": "comercial"}]}
    )

    message: str
    role: str


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Iniciar sesión",
    responses=error_responses(401),
)
def login(
    response: Response,
    email: str = Form(..., examples=["admin@crm.local"]),
    password: str = Form(...),
    session: Session = Depends(get_session),
) -> dict:
    """Valida email y contraseña (formulario) y setea la cookie HttpOnly `access_token` con el JWT.

    Credenciales inválidas → 401 con un mensaje genérico (no revela si el email existe).
    """
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


@router.post("/logout", summary="Cerrar sesión (API)")
def logout_api(response: Response) -> dict:
    """Borra la cookie de sesión en peticiones API."""
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Sesión cerrada exitosamente"}


@router.get("/logout", include_in_schema=False)
def logout_redirect():
    """Cierra la sesión y redirige a la página de login."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key=COOKIE_NAME)
    return response
