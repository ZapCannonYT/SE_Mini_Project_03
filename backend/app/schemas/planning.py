from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RecommendationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    forecast_id: int = Field(strict=True, gt=0)
    current_stock: int | None = Field(default=None, strict=True, ge=0)
    safety_stock: int | None = Field(default=None, strict=True, ge=0)
    overstock_factor: float | None = Field(default=None, ge=1, le=10)


class RecommendationOut(BaseModel):
    id: int
    product_id: int
    forecast_id: int
    current_stock: int
    forecast_demand: float
    safety_stock: int
    overstock_factor: float
    reorder_qty: int
    risk: Literal["none", "stockout", "overstock"]
    created_at: datetime


class PlanningAlertOut(BaseModel):
    product_id: int
    sku: str
    name: str
    forecast_id: int
    current_stock: int
    forecast_demand: float
    safety_stock: int
    overstock_factor: float
    reorder_qty: int
    risk: Literal["stockout", "overstock"]
