from datetime import date, timedelta

from app.models import Role, SalesRecord


def create_product(client, headers, *, sku="DASH-1", stock=4):
    response = client.post(
        "/api/products",
        json={
            "sku": sku,
            "name": "Dashboard item",
            "safety_stock": 3,
            "initial_quantity": stock,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def seed_flat_history(db, product_id, days=70, quantity=10):
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    db.add_all([
        SalesRecord(
            product_id=product_id,
            sale_date=start + timedelta(days=offset),
            quantity_sold=quantity,
        )
        for offset in range(days)
    ])
    db.commit()


def test_dashboard_matches_frontend_contract_and_planning_rules(client, db, auth_headers):
    product_id = create_product(client, auth_headers(Role.ADMIN))
    seed_flat_history(db, product_id)

    response = client.get("/api/dashboard", headers=auth_headers(Role.VIEWER))

    assert response.status_code == 200
    data = response.json()
    assert data["generated_at"]
    assert data["horizon_days"] == 7
    assert set(data["totals"]) == {
        "current_stock", "forecast_demand", "reorder_count", "stockout_count", "overstock_count", "product_count"
    }
    assert data["totals"]["product_count"] == 1
    assert data["totals"]["current_stock"] == 4
    assert data["totals"]["forecast_demand"] > 0
    item = data["items"][0]
    assert item["product_id"] == product_id
    assert item["risk"] == "stockout"
    assert item["reorder_qty"] > 0

    trend = data["trend"]
    assert len(trend) == 37
    assert all(isinstance(point["actual"], (int, float)) for point in trend[:30])
    assert trend[0]["actual"] == 10
    assert all(point["forecast"] is None for point in trend[:29])
    assert trend[29]["forecast"] == trend[29]["actual"]
    assert all(point["actual"] is None and isinstance(point["forecast"], (int, float)) for point in trend[30:])


def test_dashboard_empty_database_returns_zero_totals_and_complete_trend(client, auth_headers):
    response = client.get("/api/dashboard", headers=auth_headers(Role.VIEWER))

    assert response.status_code == 200
    data = response.json()
    assert data["totals"] == {
        "current_stock": 0,
        "forecast_demand": 0,
        "reorder_count": 0,
        "stockout_count": 0,
        "overstock_count": 0,
        "product_count": 0,
    }
    assert data["items"] == []
    assert len(data["trend"]) == 37
    assert all(point["actual"] == 0 for point in data["trend"][:30])
    assert all(point["forecast"] == 0 for point in data["trend"][30:])


def test_dashboard_product_without_sales_uses_zero_forecast(client, auth_headers):
    create_product(client, auth_headers(Role.ADMIN), stock=0)

    response = client.get("/api/dashboard", headers=auth_headers(Role.PLANNER))

    assert response.status_code == 200
    data = response.json()
    assert data["totals"]["product_count"] == 1
    assert data["totals"]["forecast_demand"] == 0
    assert data["items"][0]["forecast_demand"] == 0
    assert data["items"][0]["risk"] == "none"


def test_dashboard_requires_authentication(client):
    assert client.get("/api/dashboard").status_code == 401
