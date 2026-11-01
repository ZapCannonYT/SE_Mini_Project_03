from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=f"{settings.app_name} - Demand Forecasting & Inventory Planning API",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok"}
