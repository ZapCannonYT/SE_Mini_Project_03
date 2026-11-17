import csv
import io
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Forecast, Product, Recommendation
from app.schemas.report import PlanningReportRow

# Column order shared by the table and the CSV export (DFIP-F-019, F-020).
CSV_COLUMNS = (
    "recommendation_id",
    "sku",
    "name",
    "created_at",
    "horizon",
    "unit",
    "current_stock",
    "forecast_demand",
    "safety_stock",
    "overstock_factor",
    "reorder_qty",
    "risk",
)


def planning_report(
    db: Session,
    product_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    risk: str | None = None,
) -> list[PlanningReportRow]:
    """Stored planning recommendations matching the filters, newest first (DFIP-F-019)."""
    if start_date and end_date and start_date > end_date:
        raise AppError(
            422,
            "validation_error",
            "Some fields are missing or invalid.",
            [{"field": "start_date", "message": "Start date must be on or before end date"}],
        )

    stmt = (
        select(Recommendation, Product, Forecast)
        .join(Product, Product.id == Recommendation.product_id)
        .join(Forecast, Forecast.id == Recommendation.forecast_id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
    )
    if product_id is not None:
        stmt = stmt.where(Recommendation.product_id == product_id)
    if start_date is not None:
        stmt = stmt.where(Recommendation.created_at >= datetime.combine(start_date, time.min))
    if end_date is not None:
        stmt = stmt.where(Recommendation.created_at < datetime.combine(end_date + timedelta(days=1), time.min))
    if risk is not None:
        stmt = stmt.where(Recommendation.risk == risk)

    return [
        PlanningReportRow(
            recommendation_id=rec.id,
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            forecast_id=forecast.id,
            horizon=forecast.horizon,
            unit=forecast.unit.value,
            current_stock=rec.current_stock,
            forecast_demand=rec.forecast_demand,
            safety_stock=rec.safety_stock,
            overstock_factor=rec.overstock_factor,
            reorder_qty=rec.reorder_qty,
            risk=rec.risk.value,
            created_at=rec.created_at,
        )
        for rec, product, forecast in db.execute(stmt).all()
    ]


def _safe_cell(value) -> str:
    """Stop spreadsheet programs from running text such as '=SUM(...)' as a formula."""
    text = str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def planning_report_csv(rows: list[PlanningReportRow]) -> str:
    """CSV with the same rows, in the same order, as the report table (DFIP-F-020)."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)
    for row in rows:
        data = row.model_dump()
        writer.writerow([_safe_cell(data[c]) for c in CSV_COLUMNS])
    return out.getvalue()
