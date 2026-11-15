"""Dashboard aggregation from sales, inventory, forecasting and planning data."""
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.forecasting import forecast
from app.analytics.planning import plan
from app.analytics.preprocessing import InsufficientHistoryError, build_series
from app.models import Product, SalesRecord
from app.schemas.dashboard import DashboardOut
from app.services import inventory_service, sales_service
from app.services.planning_settings import PlanningSettings, get_planning_settings

HORIZON_DAYS = 7
ACTUAL_DAYS = 30
FALLBACK_DAYS = 28


def _forecast_demand(history: list[dict], today: date, min_periods: int) -> float:
    """Return a one-week forecast, falling back to the dashboard's 28-day average.

    The forecasting engine needs at least eight weekly periods. Sparse histories
    still get a useful dashboard estimate, matching the frontend's provisional
    calculation; a product with no sales receives a zero forecast.
    """
    if not history:
        return 0.0
    try:
        series = build_series(history, unit="week", min_periods=min_periods)
    except InsufficientHistoryError:
        cutoff = today - timedelta(days=FALLBACK_DAYS)
        recent_sales = sum(
            row["quantity_sold"] for row in history if cutoff <= row["sale_date"] < today
        )
        return round(recent_sales / FALLBACK_DAYS * HORIZON_DAYS, 1)
    result = forecast(series, horizon=1, unit="week", min_periods=min_periods)
    return round(result.points[0].predicted_qty, 1)


def build_dashboard(db: Session) -> DashboardOut:
    products: list[Product] = inventory_service.list_stock(db)
    today = date.today()
    settings: PlanningSettings = get_planning_settings(db)
    items = []

    for product in products:
        history = sales_service.get_sales_history(db, product.id)
        forecast_demand = _forecast_demand(history, today, settings.minimum_history_periods)
        current_stock = product.inventory.quantity if product.inventory else 0
        safety_stock = (
            settings.default_safety_stock
            if settings.default_safety_stock is not None
            else product.safety_stock
        )
        overstock_factor = (
            settings.default_overstock_factor
            if settings.default_overstock_factor is not None
            else product.overstock_factor
        )
        result = plan(current_stock, forecast_demand, safety_stock, overstock_factor)
        items.append({
            "product_id": product.id,
            "sku": product.sku,
            "name": product.name,
            "current_stock": current_stock,
            "forecast_demand": forecast_demand,
            "safety_stock": safety_stock,
            "overstock_factor": overstock_factor,
            "reorder_qty": result.reorder_qty,
            "risk": result.risk.value,
        })

    active_ids = [product.id for product in products]
    actual_by_date: dict[date, float] = {}
    first_actual_date = today - timedelta(days=ACTUAL_DAYS)
    last_actual_date = today - timedelta(days=1)
    if active_ids:
        rows = db.execute(
            select(SalesRecord.sale_date, func.sum(SalesRecord.quantity_sold))
            .where(
                SalesRecord.product_id.in_(active_ids),
                SalesRecord.sale_date >= first_actual_date,
                SalesRecord.sale_date <= last_actual_date,
            )
            .group_by(SalesRecord.sale_date)
        )
        actual_by_date = {sale_date: float(total) for sale_date, total in rows}

    daily_forecast = round(sum(item["forecast_demand"] for item in items) / HORIZON_DAYS, 1)
    trend = []
    for offset in range(-ACTUAL_DAYS, 0):
        point_date = today + timedelta(days=offset)
        actual = actual_by_date.get(point_date, 0.0)
        trend.append({
            "date": point_date,
            "actual": actual,
            "forecast": actual if point_date == last_actual_date else None,
        })
    for offset in range(HORIZON_DAYS):
        trend.append({
            "date": today + timedelta(days=offset),
            "actual": None,
            "forecast": daily_forecast,
        })

    return DashboardOut(
        generated_at=datetime.now(UTC),
        horizon_days=HORIZON_DAYS,
        totals={
            "current_stock": sum(item["current_stock"] for item in items),
            "forecast_demand": round(sum(item["forecast_demand"] for item in items), 1),
            "reorder_count": sum(item["reorder_qty"] > 0 for item in items),
            "stockout_count": sum(item["risk"] == "stockout" for item in items),
            "overstock_count": sum(item["risk"] == "overstock" for item in items),
            "product_count": len(items),
        },
        items=items,
        trend=trend,
    )
