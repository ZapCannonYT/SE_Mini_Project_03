"""Inventory storage and updates (DFIP-F-005, DFIP-F-006, TC-INV-01, TC-INV-02)."""
import pytest

from app.models import Role


@pytest.fixture
def admin(auth_headers):
    return auth_headers(Role.ADMIN)


@pytest.fixture
def product_id(client, admin):
    response = client.post(
        "/api/products", json={"sku": "SKU-200", "name": "Copper wire", "initial_quantity": 15}, headers=admin
    )
    return response.json()["id"]


def test_stored_quantity_is_retrievable(client, product_id, auth_headers):  # TC-INV-01
    response = client.get(f"/api/inventory/{product_id}", headers=auth_headers(Role.VIEWER))

    assert response.status_code == 200
    assert response.json()["sku"] == "SKU-200"
    assert response.json()["quantity"] == 15


def test_planner_updates_stock_and_it_persists(client, product_id, auth_headers, db):  # TC-INV-02 (valid)
    planner = auth_headers(Role.PLANNER)

    response = client.put(f"/api/inventory/{product_id}", json={"quantity": 120}, headers=planner)

    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == 120
    assert body["updated_at"] is not None
    assert body["updated_by"] is not None
    assert client.get(f"/api/inventory/{product_id}", headers=planner).json()["quantity"] == 120


@pytest.mark.parametrize("bad", [-5, "abc", "12", 1.5, True, None])
def test_invalid_quantities_are_rejected_and_stock_unchanged(client, product_id, admin, bad):  # TC-INV-02
    response = client.put(f"/api/inventory/{product_id}", json={"quantity": bad}, headers=admin)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert client.get(f"/api/inventory/{product_id}", headers=admin).json()["quantity"] == 15


def test_missing_quantity_is_rejected(client, product_id, admin):
    assert client.put(f"/api/inventory/{product_id}", json={}, headers=admin).status_code == 422


def test_viewer_cannot_update_stock(client, product_id, auth_headers):
    response = client.put(f"/api/inventory/{product_id}", json={"quantity": 1}, headers=auth_headers(Role.VIEWER))
    assert response.status_code == 403


def test_unknown_product_returns_404(client, admin):
    response = client.put("/api/inventory/999", json={"quantity": 1}, headers=admin)
    assert response.status_code == 404
    assert response.json()["code"] == "product_not_found"


def test_deactivated_product_stock_cannot_be_changed(client, product_id, admin):
    client.patch(f"/api/products/{product_id}/deactivate", headers=admin)

    response = client.put(f"/api/inventory/{product_id}", json={"quantity": 5}, headers=admin)
    assert response.status_code == 409
    assert response.json()["code"] == "product_inactive"


def test_list_shows_stock_for_active_products_only(client, product_id, admin):
    other = client.post("/api/products", json={"sku": "SKU-201", "name": "Tape"}, headers=admin).json()["id"]
    client.patch(f"/api/products/{other}/deactivate", headers=admin)

    stock = client.get("/api/inventory", headers=admin).json()
    assert [(row["sku"], row["quantity"]) for row in stock] == [("SKU-200", 15)]
