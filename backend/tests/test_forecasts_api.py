from datetime import date, timedelta

from app.models import SalesRecord


def seed_history(db, product_id: int, days: int = 70):
    start = date(2025, 1, 6)
    db.add_all([
        SalesRecord(product_id=product_id, sale_date=start + timedelta(days=offset), quantity_sold=10)
        for offset in range(days)
    ])
    db.commit()


def make_product(client, headers):
    response = client.post(
        "/api/products",
        json={"sku": "FCST-1", "name": "Forecast item", "initial_quantity": 15},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_list_forecast(client, db, auth_headers):
    # Use the existing role fixture to create an authorized planner.
    from app.models import Role
    planner = auth_headers(Role.PLANNER)
    product_id = make_product(client, auth_headers(Role.ADMIN))
    seed_history(db, product_id)

    response = client.post(
        "/api/forecasts", json={"product_id": product_id, "horizon": 4, "unit": "week"}, headers=planner
    )
    assert response.status_code == 201
    result = response.json()
    assert result["product_id"] == product_id
    assert result["horizon"] == 4
    assert len(result["points"]) == 4
    assert result["model_name"]
    assert result["model_version"]

    listed = client.get("/api/forecasts", params={"product_id": product_id}, headers=planner)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [result["id"]]
    fetched = client.get(f"/api/forecasts/{result['id']}", headers=planner)
    assert fetched.status_code == 200
    assert fetched.json() == result


def test_forecast_reports_insufficient_history(client, auth_headers):
    from app.models import Role
    product_id = make_product(client, auth_headers(Role.ADMIN))
    response = client.post(
        "/api/forecasts", json={"product_id": product_id, "horizon": 4, "unit": "week"},
        headers=auth_headers(Role.PLANNER),
    )
    assert response.status_code == 422
    assert response.json()["code"] == "insufficient_history"


def test_forecast_invalid_horizon_uses_shared_error_shape(client, db, auth_headers):
    from app.models import Role
    product_id = make_product(client, auth_headers(Role.ADMIN))
    seed_history(db, product_id)
    response = client.post(
        "/api/forecasts", json={"product_id": product_id, "horizon": 13, "unit": "week"},
        headers=auth_headers(Role.PLANNER),
    )
    assert response.status_code == 400
    assert set(response.json()) == {"code", "message", "details"}
    assert response.json()["code"] == "invalid_forecast_request"

    response = client.post(
        "/api/forecasts", json={"product_id": product_id, "horizon": 0, "unit": "week"},
        headers=auth_headers(Role.PLANNER),
    )
    assert response.status_code == 400


def test_forecast_requires_authentication(client):
    response = client.get("/api/forecasts")
    assert response.status_code == 401
