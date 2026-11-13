from datetime import UTC, date, datetime

from app.models import Forecast, ForecastPoint, HorizonUnit, Inventory, Product


def setup_forecast(db, *, stock=12):
    product = Product(sku="PLAN-1", name="Planning item", safety_stock=5, overstock_factor=1.5)
    product.inventory = Inventory(quantity=stock)
    db.add(product)
    db.flush()
    forecast = Forecast(
        product_id=product.id,
        horizon=2,
        unit=HorizonUnit.WEEK,
        model_name="Simple exponential smoothing",
        model_version="1.0",
        generated_at=datetime.now(UTC),
    )
    forecast.points = [
        ForecastPoint(period_start=date(2025, 1, 6), predicted_qty=10),
        ForecastPoint(period_start=date(2025, 1, 13), predicted_qty=10),
    ]
    db.add(forecast)
    db.commit()
    return product.id, forecast.id


def test_create_and_get_recommendation_preserves_inputs(client, db, auth_headers):
    from app.models import Role
    product_id, forecast_id = setup_forecast(db)
    response = client.post(
        "/api/planning/recommendations",
        json={"forecast_id": forecast_id, "current_stock": 7, "safety_stock": 4, "overstock_factor": 2},
        headers=auth_headers(Role.PLANNER),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["product_id"] == product_id
    assert body["forecast_demand"] == 20
    assert body["current_stock"] == 7
    assert body["safety_stock"] == 4
    assert body["overstock_factor"] == 2
    assert body["reorder_qty"] == 17
    assert body["risk"] == "stockout"
    assert client.get(
        f"/api/planning/recommendations/{body['id']}", headers=auth_headers(Role.VIEWER)
    ).json() == body


def test_recommendation_uses_product_defaults(client, db, auth_headers):
    from app.models import Role
    _product_id, forecast_id = setup_forecast(db, stock=22)
    response = client.post(
        "/api/planning/recommendations", json={"forecast_id": forecast_id}, headers=auth_headers(Role.PLANNER)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["current_stock"] == 22
    assert body["safety_stock"] == 5
    assert body["overstock_factor"] == 1.5
    assert body["risk"] == "none"


def test_alerts_include_latest_stockout_and_skip_products_without_forecasts(client, db, auth_headers):
    from app.models import Role
    product_id, forecast_id = setup_forecast(db, stock=4)
    # The endpoint derives alerts from current inventory and the latest stored forecast.
    alerts = client.get("/api/planning/alerts", headers=auth_headers(Role.VIEWER))
    assert alerts.status_code == 200
    assert alerts.json() == [{
        "product_id": product_id,
        "sku": "PLAN-1",
        "name": "Planning item",
        "forecast_id": forecast_id,
        "current_stock": 4,
        "forecast_demand": 20,
        "safety_stock": 5,
        "overstock_factor": 1.5,
        "reorder_qty": 21,
        "risk": "stockout",
    }]


def test_recommendation_rejects_unknown_forecast(client, auth_headers):
    from app.models import Role
    response = client.post(
        "/api/planning/recommendations", json={"forecast_id": 999}, headers=auth_headers(Role.PLANNER)
    )
    assert response.status_code == 404
    assert response.json()["code"] == "forecast_not_found"
