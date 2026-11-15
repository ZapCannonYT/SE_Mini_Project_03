from datetime import date, datetime

from pydantic import BaseModel


class DashboardTotals(BaseModel):
    current_stock: int
    forecast_demand: float
    reorder_count: int
    stockout_count: int
    overstock_count: int
    product_count: int


class DashboardItem(BaseModel):
    product_id: int
    sku: str
    name: str
    current_stock: int
    forecast_demand: float
    safety_stock: int
    overstock_factor: float
    reorder_qty: int
    risk: str


class DashboardTrendPoint(BaseModel):
    date: date
    actual: float | None
    forecast: float | None


class DashboardOut(BaseModel):
    generated_at: datetime
    horizon_days: int
    totals: DashboardTotals
    items: list[DashboardItem]
    trend: list[DashboardTrendPoint]
