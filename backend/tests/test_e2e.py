"""End-to-end flow (STP system testing): login -> products -> import sales -> view history.

Forecast, plan and report steps are added once #33 (forecast, planning and alerts API) and #38 (reports) merge.
"""
from pathlib import Path

from app.core.config import settings
from app.models import Role

SAMPLES = Path(__file__).resolve().parents[2] / "data" / "samples"


def login(client, email, password) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_sets_up_data_and_planner_imports_sales(client):  # E2E flow
    # 1. Admin logs in with the seeded account and creates a planner and a viewer.
    admin = login(client, settings.admin_email, "Admin@123")
    for name, role in (("Pat", "planner"), ("Val", "viewer")):
        user = {"name": name, "email": f"{name.lower()}@example.com", "password": "Passw0rd!", "role": role}
        assert client.post("/api/users", json=user, headers=admin).status_code == 201

    # 2. Admin creates the products used by the sample files, with starting stock.
    for sku, stock in (("SKU-100", 40), ("SKU-200", 120)):
        product = {"sku": sku, "name": f"Product {sku}", "safety_stock": 10, "initial_quantity": stock}
        assert client.post("/api/products", json=product, headers=admin).status_code == 201

    # 3. Planner logs in, imports the sample sales history and adds one day by hand.
    planner = login(client, "pat@example.com", "Passw0rd!")
    with open(SAMPLES / "valid_sales.csv", "rb") as f:
        imported = client.post("/api/sales/import", files={"file": ("valid_sales.csv", f, "text/csv")}, headers=planner)
    assert imported.json() == {"imported": 20, "rejected": []}
    products = {p["sku"]: p["id"] for p in client.get("/api/products", headers=planner).json()}
    manual = {"product_id": products["SKU-100"], "sale_date": "2026-09-11", "quantity_sold": 8}
    assert client.post("/api/sales", json=manual, headers=planner).status_code == 201

    # 4. Planner records a stock count.
    assert client.put(f"/api/inventory/{products['SKU-100']}", json={"quantity": 35}, headers=planner).status_code == 200

    # 5. Viewer sees the same data but cannot change it.
    viewer = login(client, "val@example.com", "Passw0rd!")
    history = client.get(
        "/api/sales", params={"product_id": products["SKU-100"], "start_date": "2026-09-01"}, headers=viewer
    ).json()
    assert len(history) == 11
    assert history[0]["sale_date"] == "2026-09-11"
    stock = {i["sku"]: i["quantity"] for i in client.get("/api/inventory", headers=viewer).json()}
    assert stock == {"SKU-100": 35, "SKU-200": 120}
    assert client.post("/api/sales", json=manual, headers=viewer).status_code == 403

    # 6. Logging out ends the session on the client side; the API still requires a token.
    assert client.post("/api/auth/logout", headers=planner).status_code == 200
    assert client.get("/api/sales").status_code == 401


def test_roles_see_only_what_they_may_change(client, auth_headers):  # E2E flow, DFIP-SR-004
    admin = auth_headers(Role.ADMIN)
    product_id = client.post("/api/products", json={"sku": "SKU-1", "name": "Bolts"}, headers=admin).json()["id"]
    sale = {"product_id": product_id, "sale_date": "2026-09-01", "quantity_sold": 1}

    expected = {
        Role.ADMIN: {"product": 201, "stock": 200, "sale": 201, "users": 200},
        Role.PLANNER: {"product": 403, "stock": 200, "sale": 409, "users": 403},
        Role.VIEWER: {"product": 403, "stock": 403, "sale": 403, "users": 403},
    }
    for role, codes in expected.items():
        h = auth_headers(role)
        actual = {
            "product": client.post("/api/products", json={"sku": f"N-{role.value}", "name": "x"}, headers=h).status_code,
            "stock": client.put(f"/api/inventory/{product_id}", json={"quantity": 5}, headers=h).status_code,
            "sale": client.post("/api/sales", json=sale, headers=h).status_code,
            "users": client.get("/api/users", headers=h).status_code,
        }
        assert actual == codes, role
