"""Product/SKU management API (DFIP-F-004, TC-PROD-01)."""
import pytest

from app.models import Role

NEW_PRODUCT = {"sku": "SKU-100", "name": "Steel bolts", "category": "Hardware", "safety_stock": 20}


@pytest.fixture
def admin(auth_headers):
    return auth_headers(Role.ADMIN)


def create(client, admin, **overrides):
    return client.post("/api/products", json={**NEW_PRODUCT, **overrides}, headers=admin)


def test_admin_creates_product_and_it_appears_in_list(client, admin, auth_headers):  # TC-PROD-01
    response = create(client, admin, initial_quantity=40)

    assert response.status_code == 201
    product = response.json()
    assert product["sku"] == "SKU-100"
    assert product["safety_stock"] == 20
    assert product["overstock_factor"] == 1.5
    assert product["quantity"] == 40
    assert product["is_active"] is True

    listed = client.get("/api/products", headers=auth_headers(Role.VIEWER)).json()
    assert [p["sku"] for p in listed] == ["SKU-100"]


def test_new_product_starts_with_zero_stock_by_default(client, admin):
    assert create(client, admin).json()["quantity"] == 0


def test_duplicate_sku_is_rejected_case_insensitively(client, admin):
    create(client, admin)
    response = create(client, admin, sku="sku-100")

    assert response.status_code == 409
    assert response.json()["code"] == "sku_exists"


@pytest.mark.parametrize(
    "field,value",
    [
        ("sku", "bad sku!"),
        ("sku", ""),
        ("name", "   "),
        ("safety_stock", -1),
        ("safety_stock", 2.5),
        ("overstock_factor", 0),
        ("initial_quantity", -10),
    ],
)
def test_invalid_fields_are_rejected_with_clear_message(client, admin, field, value):
    response = create(client, admin, **{field: value})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["details"][0]["field"] == field


def test_unknown_fields_are_rejected(client, admin):
    assert create(client, admin, price=10).status_code == 422


@pytest.mark.parametrize("role", [Role.PLANNER, Role.VIEWER])
def test_only_admin_can_create(client, auth_headers, role):
    response = client.post("/api/products", json=NEW_PRODUCT, headers=auth_headers(role))
    assert response.status_code == 403


def test_requests_without_token_are_rejected(client):
    assert client.get("/api/products").status_code == 401
    assert client.post("/api/products", json=NEW_PRODUCT).status_code == 401


def test_get_single_product(client, admin, auth_headers):
    product_id = create(client, admin).json()["id"]

    response = client.get(f"/api/products/{product_id}", headers=auth_headers(Role.PLANNER))
    assert response.status_code == 200
    assert response.json()["name"] == "Steel bolts"


def test_get_missing_product_returns_404(client, admin):
    response = client.get("/api/products/999", headers=admin)
    assert response.status_code == 404
    assert response.json()["code"] == "product_not_found"


def test_update_changes_only_sent_fields(client, admin):
    product_id = create(client, admin).json()["id"]

    response = client.put(f"/api/products/{product_id}", json={"name": "Zinc bolts", "safety_stock": 35}, headers=admin)

    assert response.status_code == 200
    updated = response.json()
    assert (updated["name"], updated["safety_stock"], updated["category"]) == ("Zinc bolts", 35, "Hardware")


def test_update_cannot_change_sku_or_blank_required_fields(client, admin):
    product_id = create(client, admin).json()["id"]

    assert client.put(f"/api/products/{product_id}", json={"sku": "NEW"}, headers=admin).status_code == 422
    response = client.put(f"/api/products/{product_id}", json={"name": None}, headers=admin)
    assert response.status_code == 422
    assert response.json()["details"][0]["field"] == "name"


def test_planner_cannot_update(client, admin, auth_headers):
    product_id = create(client, admin).json()["id"]
    response = client.put(f"/api/products/{product_id}", json={"name": "X"}, headers=auth_headers(Role.PLANNER))
    assert response.status_code == 403


def test_deactivated_product_is_hidden_from_default_list(client, admin):
    product_id = create(client, admin).json()["id"]

    response = client.patch(f"/api/products/{product_id}/deactivate", headers=admin)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    assert client.get("/api/products", headers=admin).json() == []
    all_products = client.get("/api/products", params={"include_inactive": True}, headers=admin).json()
    assert [p["id"] for p in all_products] == [product_id]
