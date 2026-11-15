
from app.models import Role


def test_admin_can_get_default_settings(client, auth_headers):
    response = client.get(
        "/api/settings",
        headers=auth_headers(Role.ADMIN),
    )

    assert response.status_code == 200
    assert response.json()["minimum_history_periods"] == 8
    assert response.json()["default_safety_stock"] is None
    assert response.json()["default_overstock_factor"] is None


def test_admin_can_update_settings(client, auth_headers):
    response = client.patch(
        "/api/settings",
        headers=auth_headers(Role.ADMIN),
        json={
            "default_safety_stock": 10,
            "default_overstock_factor": 2.5,
            "minimum_history_periods": 12,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["default_safety_stock"] == 10
    assert data["default_overstock_factor"] == 2.5
    assert data["minimum_history_periods"] == 12


def test_planner_cannot_update_settings(client, auth_headers):
    response = client.patch(
        "/api/settings",
        headers=auth_headers(Role.PLANNER),
        json={"minimum_history_periods": 12},
    )

    assert response.status_code == 403


def test_viewer_cannot_get_settings(client, auth_headers):
    response = client.get(
        "/api/settings",
        headers=auth_headers(Role.VIEWER),
    )

    assert response.status_code == 403


def test_settings_reject_invalid_values(client, auth_headers):
    response = client.patch(
        "/api/settings",
        headers=auth_headers(Role.ADMIN),
        json={"default_safety_stock": -5},
    )

    assert response.status_code == 422


def test_settings_reject_empty_update(client, auth_headers):
    response = client.patch(
        "/api/settings",
        headers=auth_headers(Role.ADMIN),
        json={},
    )

    assert response.status_code == 400


def test_settings_require_authentication(client):
    response = client.get("/api/settings")

    assert response.status_code == 401

def test_settings_persist_after_update(client, auth_headers):
    headers = auth_headers(Role.ADMIN)

    client.patch(
        "/api/settings",
        headers=headers,
        json={"minimum_history_periods": 15},
    )

    response = client.get("/api/settings", headers=headers)

    assert response.status_code == 200
    assert response.json()["minimum_history_periods"] == 15


def test_settings_reject_invalid_overstock_factor(client, auth_headers):
    response = client.patch(
        "/api/settings",
        headers=auth_headers(Role.ADMIN),
        json={"default_overstock_factor": 11},
    )

    assert response.status_code == 422


def test_settings_reject_zero_history_periods(client, auth_headers):
    response = client.patch(
        "/api/settings",
        headers=auth_headers(Role.ADMIN),
        json={"minimum_history_periods": 0},
    )

    assert response.status_code == 422

