import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import COOKIE_NAME
from app.services.deal_service import calculate_win_probability

client = TestClient(app)

# 1. Prueba de reglas de probabilidad de Deals (deal_service)
def test_calculate_win_probability():
    """Verifica que el cálculo de probabilidad devuelva valores numéricos válidos."""
    prob_lead = calculate_win_probability("lead")
    prob_won = calculate_win_probability("won")
    prob_lost = calculate_win_probability("lost")
    
    assert prob_lead >= 0
    assert prob_won == 100
    assert prob_lost == 0

# 2. Prueba del endpoint de Logout (Auth)
def test_logout_clears_cookie():
    """Verifica que el endpoint de logout redirija y borre la cookie de acceso."""
    response = client.get("/api/auth/logout", follow_redirects=False)
    
    # Debe responder con redirección (303)
    assert response.status_code == 303
    # Debe incluir la instrucción de borrar la cookie HttpOnly
    assert COOKIE_NAME in response.headers.get("set-cookie", "")

# 3. Prueba de acceso no autorizado
def test_protected_route_requires_auth():
    """Verifica que rutas protegidas rechacen solicitudes sin credenciales."""
    response = client.get("/api/customers")
    # Al no llevar cookie de autenticación, debe negar el acceso o redirigir a login
    assert response.status_code in [401, 303, 307]