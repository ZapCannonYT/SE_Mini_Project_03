from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PlanningReportRow(BaseModel):
    recommendation_id: int
    product_id: int
    sku: str
    name: str
    forecast_id: int
    horizon: int
    unit: Literal["week", "month"]
    current_stock: int
    forecast_demand: float
    safety_stock: int
    overstock_factor: float
    reorder_qty: int
    risk: Literal["none", "stockout", "overstock"]
    created_at: datetime
