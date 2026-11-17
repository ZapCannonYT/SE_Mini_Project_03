
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    audit,
    dashboard,
    forecasts,
    inventory,
    planning,
    products,
    sales,
    users,
)

from app.api import settings as settings_api

from app.core.config import settings
from app.core.db import init_db
from app.core.errors import register_error_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=f"{settings.app_name} - Demand Forecasting & Inventory Planning API",
    version="0.1.0",
    lifespan=lifespan,
)

register_error_handlers(app)

# CORS is limited to the configured frontend origins (SR-005); no wildcard.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(auth.router)
app.include_router(audit.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(users.router)
app.include_router(settings_api.router)
app.include_router(forecasts.router)
app.include_router(planning.router)
app.include_router(dashboard.router)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok"}
