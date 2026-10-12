from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.database import init_db
from app.routers import (
    auth,
    customers,
    deals,
    health,
    insight_pages,
    interactions,
    pages,
    task_pages,
    tasks,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


API_DESCRIPTION = """
API REST del **CRM Inteligente**: clientes, interacciones, pipeline de ventas, tareas de
seguimiento y analítica comercial con IA (Google Gemini).

### Autenticación
`POST /api/auth/login` valida las credenciales y entrega el JWT en la cookie **HttpOnly**
`access_token` (60 min). El navegador la envía sola en cada petición, así que en esta
página basta con iniciar sesión antes en [`/login`](/login) y usar *Try it out*.

### Roles (RBAC)
- **comercial**: lectura de todo y operación diaria (interacciones, deals, tareas propias, tags, IA).
- **admin**: además, alta/edición/baja de clientes, borrado de deals, tareas y tags, y asignación de tareas a otros usuarios.

### Errores
Todos los errores controlados responden `{"detail": "<mensaje>"}`. Los endpoints de IA
devuelven **502** si Gemini falla tras el reintento automático (timeout de 25 s por intento).
"""

OPENAPI_TAGS = [
    {"name": "auth", "description": "Inicio de sesión con JWT en cookie HttpOnly."},
    {"name": "customers", "description": "Clientes, sus tags y los análisis de IA (resumen, sugerencias de venta, insights)."},
    {"name": "interactions", "description": "Historial de interacciones (llamadas, correos, reuniones, tickets) de un cliente."},
    {"name": "deals", "description": "Oportunidades del pipeline de ventas y cambio de etapa."},
    {"name": "tasks", "description": "Tareas de seguimiento por cliente y por usuario asignado."},
    {"name": "health", "description": "Estado del servicio y de la conexión a PostgreSQL."},
]

app = FastAPI(
    title="CRM Inteligente API",
    description=API_DESCRIPTION,
    version="1.0.0",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Páginas y fragmentos HTMX devuelven HTML para la interfaz: no forman parte de la API documentada.
app.include_router(pages.router, include_in_schema=False)
app.include_router(insight_pages.router, include_in_schema=False)
app.include_router(task_pages.router, include_in_schema=False)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(interactions.router)
app.include_router(deals.router)
app.include_router(tasks.router)
