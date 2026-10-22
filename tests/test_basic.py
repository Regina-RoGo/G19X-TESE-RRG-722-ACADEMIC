import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from sqlmodel import select
from app.services import auth_service

from app.main import app
from app.models.deal import Deal, DealStage
from app.models.user import User, UserRole
from app.core.security import create_access_token, hash_password
from app.core.database import get_session, engine  # <--- ASEGÚRATE DE INCLUIR 'engine' AQUÍ
from app.services.deal_service import _apply_stage_rules, OPEN_STAGE_DEFAULT_PROBABILITY

client = TestClient(app)

# ----------------------------------------------------------------------
# 1. PRUEBA DE LÓGICA DE NEGOCIO (Reglas de etapas de Deals)
# ----------------------------------------------------------------------
def test_deal_stage_rules():
    """Verifica que las reglas de negocio de probabilidades se apliquen correctamente."""
    # Objeto simulado de un deal en Prospecto
    mock_deal = Deal(
        title="Deal de Prueba",
        value=1000.0,
        stage=DealStage.PROSPECT,
        probability=10,
        customer_id=1
    )
    
    # Al pasar a CLOSED_WON la probabilidad debe ser forzosamente 100%
    mock_deal.stage = DealStage.CLOSED_WON
    _apply_stage_rules(mock_deal, previous_stage=DealStage.PROSPECT, probability_given=None)
    assert mock_deal.probability == 100

    # Al pasar a CLOSED_LOST la probabilidad debe ser 0%
    mock_deal.stage = DealStage.CLOSED_LOST
    _apply_stage_rules(mock_deal, previous_stage=DealStage.CLOSED_WON, probability_given=None)
    assert mock_deal.probability == 0

    # Al reabrir un deal a PROSPECT sin probabilidad explícita, usa la probabilidad base
    mock_deal.stage = DealStage.PROSPECT
    _apply_stage_rules(mock_deal, previous_stage=DealStage.CLOSED_LOST, probability_given=None)
    assert mock_deal.probability == OPEN_STAGE_DEFAULT_PROBABILITY[DealStage.PROSPECT]


# ----------------------------------------------------------------------
# 2. PRUEBA DE PROTECCIÓN DE RUTAS (Sin cookie -> 401 / 303)
# ----------------------------------------------------------------------
def test_unauthenticated_access_protection():
    """Peticiones a la API sin token devuelven 401; las páginas redirigen."""
    # Endpoint API sin token -> 401
    response_api = client.get("/api/customers/")
    assert response_api.status_code == 401

    # Página protegida sin token -> 303 (redirección a /login)
    response_page = client.get("/customers", follow_redirects=False)
    assert response_page.status_code == 303
    assert response_page.headers["location"] == "/login"


# ----------------------------------------------------------------------
# 3. PRUEBA DE RBAC (Comercial recibe 403 en acciones restringidas)
# ----------------------------------------------------------------------
def test_comercial_role_forbidden_action():
    """Un usuario con rol comercial debe recibir 403 al intentar eliminar recursos."""
    # Insertamos un usuario comercial real en la base de datos de pruebas usando SQLModel
    with Session(engine) as session:
        statement = select(User).where(User.email == "comercial_test@crm.local")
        user = session.exec(statement).first()
        if not user:
            user = User(
                full_name="Comercial Test",
                email="comercial_test@crm.local",
                hashed_password=hash_password("Password123!"),
                role=UserRole.COMERCIAL
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        
        # Usamos el servicio oficial de la app para crear el token exacto
        token_comercial = auth_service.create_user_token(user)

    # Asignamos la cookie con el token válido
    client.cookies.set("access_token", token_comercial)

    # Intentar eliminar un deal (endpoint protegido solo para admin) -> Debe dar 403
    response = client.delete("/api/deals/1")
    assert response.status_code == 403
    
    # Limpiamos las cookies
    client.cookies.clear()

# ----------------------------------------------------------------------
# 4. PRUEBA DE LOGOUT Y EXPIRACIÓN DE SESIÓN
# ----------------------------------------------------------------------
def test_logout_clears_cookie():
    """El endpoint de logout debe responder con 200 y limpiar la cookie access_token."""
    # Simulamos estar autenticados
    token = create_access_token(data={"sub": 1, "role": UserRole.ADMIN})
    client.cookies.set("access_token", token)

    # Hacemos POST a logout (o endpoint correspondiente)
    response = client.post("/api/auth/logout")
    
    # Debe responder exitosamente y borrar/invalidar la cookie
    assert response.status_code == 200
    # Verificamos que la cookie 'access_token' en el Set-Cookie esté vacía o expirada
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie_header or "access_token" not in client.cookies