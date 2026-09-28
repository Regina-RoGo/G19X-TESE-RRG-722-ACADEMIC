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


app = FastAPI(title="CRM Inteligente", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
app.include_router(insight_pages.router)
app.include_router(task_pages.router)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(interactions.router)
app.include_router(deals.router)
app.include_router(tasks.router)
