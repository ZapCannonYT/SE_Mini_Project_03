from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.planning import demand_from_forecast, plan
from app.api.auth import require_role
from app.core.db import get_db
from app.core.errors import AppError
from app.models import (
    Forecast,
    Inventory,
    Product,
    Recommendation,
    RiskLevel,
    Role,
    User,
)
from app.schemas.planning import (
    PlanningAlertOut,
    RecommendationCreate,
    RecommendationOut,
)
from app.services.planning_settings import get_planning_settings

router = APIRouter(prefix="/api/planning", tags=["Planning"])
any_user = require_role(Role.ADMIN.value, Role.PLANNER.value, Role.VIEWER.value)
can_plan = require_role(Role.ADMIN.value, Role.PLANNER.value)


def recommendation_out(item: Recommendation) -> RecommendationOut:
    return RecommendationOut(
        id=item.id,
        product_id=item.product_id,
        forecast_id=item.forecast_id,
        current_stock=item.current_stock,
        forecast_demand=item.forecast_demand,
        safety_stock=item.safety_stock,
        overstock_factor=item.overstock_factor,
        reorder_qty=item.reorder_qty,
        risk=item.risk.value,
        created_at=item.created_at,
    )


@router.post("/recommendations", response_model=RecommendationOut, status_code=201)
def create_recommendation(
    data: RecommendationCreate, db: Session = Depends(get_db), _user: User = Depends(can_plan)
):
    forecast_record = db.get(Forecast, data.forecast_id)
    if forecast_record is None:
        raise AppError(404, "forecast_not_found", f"Forecast {data.forecast_id} does not exist.")
    product = db.get(Product, forecast_record.product_id)
    if product is None or not product.is_active:
        raise AppError(404, "product_not_found", f"Active product {forecast_record.product_id} does not exist.")
    inventory = db.get(Inventory, product.id)
    settings = get_planning_settings(db)
    current_stock = data.current_stock if data.current_stock is not None else (inventory.quantity if inventory else 0)
    safety_stock = (
        data.safety_stock
        if data.safety_stock is not None
        else settings.default_safety_stock
        if settings.default_safety_stock is not None
        else product.safety_stock
    )
    overstock_factor = (
        data.overstock_factor
        if data.overstock_factor is not None
        else settings.default_overstock_factor
        if settings.default_overstock_factor is not None
        else product.overstock_factor
    )
    forecast_demand = demand_from_forecast(forecast_record.points)
    result = plan(current_stock, forecast_demand, safety_stock, overstock_factor)
    item = Recommendation(
        product_id=product.id,
        forecast_id=forecast_record.id,
        current_stock=current_stock,
        forecast_demand=forecast_demand,
        safety_stock=safety_stock,
        overstock_factor=overstock_factor,
        reorder_qty=result.reorder_qty,
        risk=RiskLevel(result.risk.value),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return recommendation_out(item)


@router.get("/recommendations/{recommendation_id}", response_model=RecommendationOut)
def get_recommendation(
    recommendation_id: int, db: Session = Depends(get_db), _user: User = Depends(any_user)
):
    item = db.get(Recommendation, recommendation_id)
    if item is None:
        raise AppError(404, "recommendation_not_found", f"Recommendation {recommendation_id} does not exist.")
    return recommendation_out(item)


@router.get("/alerts", response_model=list[PlanningAlertOut])
def list_alerts(db: Session = Depends(get_db), _user: User = Depends(any_user)):
    settings = get_planning_settings(db)
    products = db.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.sku)).all()
    alerts = []
    for product in products:
        forecast_record = db.scalar(
            select(Forecast).where(Forecast.product_id == product.id)
            .order_by(Forecast.generated_at.desc(), Forecast.id.desc()).limit(1)
        )
        if forecast_record is None:
            continue
        inventory = db.get(Inventory, product.id)
        current_stock = inventory.quantity if inventory else 0
        forecast_demand = demand_from_forecast(forecast_record.points)
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
        if result.risk.value == "none":
            continue
        alerts.append(PlanningAlertOut(
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            forecast_id=forecast_record.id,
            current_stock=current_stock,
            forecast_demand=forecast_demand,
            safety_stock=safety_stock,
            overstock_factor=overstock_factor,
            reorder_qty=result.reorder_qty,
            risk=result.risk.value,
        ))
    return alerts
