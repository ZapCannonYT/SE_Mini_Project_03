from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.analytics.forecasting import forecast, validate_horizon
from app.analytics.preprocessing import InsufficientHistoryError, build_series
from app.api.auth import require_role
from app.core.db import get_db
from app.core.errors import AppError
from app.models import (
    Forecast,
    ForecastPoint,
    HorizonUnit,
    Product,
    Role,
    SalesRecord,
    User,
)
from app.schemas.forecast import ForecastCreate, ForecastOut
from app.services.planning_settings import get_planning_settings

router = APIRouter(prefix="/api/forecasts", tags=["Forecasts"])
any_user = require_role(Role.ADMIN.value, Role.PLANNER.value, Role.VIEWER.value)
can_create = require_role(Role.ADMIN.value, Role.PLANNER.value)


def to_out(item: Forecast) -> ForecastOut:
    return ForecastOut(
        id=item.id,
        product_id=item.product_id,
        horizon=item.horizon,
        unit=item.unit.value,
        model_name=item.model_name,
        model_version=item.model_version,
        generated_at=item.generated_at,
        points=[{"period_start": point.period_start, "predicted_qty": point.predicted_qty} for point in item.points],
    )


@router.post("", response_model=ForecastOut, status_code=status.HTTP_201_CREATED)
def create_forecast(data: ForecastCreate, db: Session = Depends(get_db), user: User = Depends(can_create)):
    try:
        validate_horizon(data.horizon, data.unit)
    except ValueError as exc:
        raise AppError(400, "invalid_forecast_request", str(exc)) from None

    product = db.get(Product, data.product_id)
    if product is None or not product.is_active:
        raise AppError(404, "product_not_found", f"Active product {data.product_id} does not exist.")

    rows = db.scalars(
        select(SalesRecord).where(SalesRecord.product_id == product.id).order_by(SalesRecord.sale_date)
    ).all()
    minimum_history = get_planning_settings(db).minimum_history_periods
    try:
        series = build_series(
            [{"sale_date": row.sale_date, "quantity_sold": row.quantity_sold} for row in rows],
            unit=data.unit,
            min_periods=minimum_history,
        )
    except InsufficientHistoryError as exc:
        raise AppError(422, "insufficient_history", str(exc)) from None
    except ValueError as exc:
        raise AppError(400, "invalid_forecast_request", str(exc)) from None

    result = forecast(series, data.horizon, data.unit, min_periods=minimum_history)
    record = Forecast(
        product_id=product.id,
        horizon=data.horizon,
        unit=HorizonUnit(data.unit),
        model_name=result.model_name,
        model_version=result.model_version,
        generated_at=result.generated_at,
        created_by=user.id,
        points=[ForecastPoint(period_start=point.period_start, predicted_qty=point.predicted_qty) for point in result.points],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_out(record)


@router.get("", response_model=list[ForecastOut])
def list_forecasts(
    product_id: int | None = Query(None, gt=0),
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
):
    stmt = select(Forecast).options(selectinload(Forecast.points)).order_by(Forecast.generated_at.desc(), Forecast.id.desc())
    if product_id is not None:
        stmt = stmt.where(Forecast.product_id == product_id)
    return [to_out(item) for item in db.scalars(stmt).all()]


@router.get("/{forecast_id}", response_model=ForecastOut)
def get_forecast(forecast_id: int, db: Session = Depends(get_db), _user: User = Depends(any_user)):
    item = db.scalar(select(Forecast).options(selectinload(Forecast.points)).where(Forecast.id == forecast_id))
    if item is None:
        raise AppError(404, "forecast_not_found", f"Forecast {forecast_id} does not exist.")
    return to_out(item)
