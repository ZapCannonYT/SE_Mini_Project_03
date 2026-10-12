from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth, users 
from app.core.config import settings
from app.core.db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=f"{settings.app_name} - Demand Forecasting & Inventory Planning API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok"}