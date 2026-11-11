"""TC-REL-01 (DFIP-NF-003): committed data survives a normal application restart."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.db import get_db, init_db, make_engine
from app.main import app


class RunningApp:
    """The API on a SQLite file, started the way the real app starts (tables + admin seeded by init_db)."""

    def __init__(self, url: str):
        self.engine = make_engine(url)
        init_db(self.engine)
        sessions = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

        def get_file_db():
            db = sessions()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = get_file_db
        self.client = TestClient(app)

    def login(self, email=None, password=None) -> dict:
        response = self.client.post(
            "/api/auth/login",
            json={"email": email or settings.admin_email, "password": password or settings.admin_password},
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def stop(self):
        self.client.close()
        self.engine.dispose()  # drop every pooled connection, as a process exit would


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{(tmp_path / 'dfip.db').as_posix()}"


def snapshot(running: RunningApp, headers: dict) -> dict:
    """Everything a user can read back through the API."""
    get = lambda path: running.client.get(path, headers=headers).json()  # noqa: E731
    return {
        "products": get("/api/products?include_inactive=true"),
        "inventory": get("/api/inventory"),
        "sales": get("/api/sales"),
        "users": get("/api/users"),
    }


def test_committed_records_survive_restart(db_url):  # TC-REL-01
    first = RunningApp(db_url)
    admin = first.login()
    c = first.client

    bolts = c.post("/api/products", json={"sku": "SKU-100", "name": "Steel bolts", "initial_quantity": 10}, headers=admin)
    wire = c.post("/api/products", json={"sku": "SKU-200", "name": "Copper wire"}, headers=admin)
    old = c.post("/api/products", json={"sku": "SKU-300", "name": "Old part"}, headers=admin)
    assert {bolts.status_code, wire.status_code, old.status_code} == {201}
    bolts_id = bolts.json()["id"]

    # Create, then modify, so both kinds of change are checked after the restart.
    assert c.put(f"/api/products/{bolts_id}", json={"name": "Zinc bolts"}, headers=admin).status_code == 200
    assert c.put(f"/api/inventory/{bolts_id}", json={"quantity": 25}, headers=admin).status_code == 200
    assert c.patch(f"/api/products/{old.json()['id']}/deactivate", headers=admin).status_code == 200
    sale = {"product_id": bolts_id, "sale_date": "2026-09-01", "quantity_sold": 7}
    assert c.post("/api/sales", json=sale, headers=admin).status_code == 201
    csv = b"sku,date,quantity_sold\nSKU-100,2026-09-02,4\nSKU-200,2026-09-02,9\n"
    imported = c.post("/api/sales/import", files={"file": ("s.csv", csv, "text/csv")}, headers=admin)
    assert imported.json() == {"imported": 2, "rejected": []}
    # @example.com: user creation rejects @dfip.local until defect #61 is fixed.
    planner = {"name": "Pat Planner", "email": "pat@example.com", "password": "Planner@123", "role": "planner"}
    assert c.post("/api/users", json=planner, headers=admin).status_code == 201

    before = snapshot(first, admin)
    first.stop()

    second = RunningApp(db_url)
    admin_again = second.login()
    after = snapshot(second, admin_again)

    assert after == before
    assert next(p for p in after["products"] if p["id"] == bolts_id)["name"] == "Zinc bolts"
    assert next(i for i in after["inventory"] if i["product_id"] == bolts_id)["quantity"] == 25
    assert len(after["sales"]) == 3
    assert [p["is_active"] for p in after["products"] if p["sku"] == "SKU-300"] == [False]
    # The user created before the restart can still log in and use the API.
    assert second.client.get("/api/sales", headers=second.login("pat@example.com", "Planner@123")).status_code == 200
    second.stop()


def test_rejected_requests_leave_nothing_behind_after_restart(db_url):  # TC-REL-01
    first = RunningApp(db_url)
    admin = first.login()
    c = first.client
    product_id = c.post("/api/products", json={"sku": "SKU-100", "name": "Bolts"}, headers=admin).json()["id"]

    bad_csv = b"sku,day,quantity_sold\nSKU-100,2026-09-01,4\n"
    assert c.post("/api/sales/import", files={"file": ("s.csv", bad_csv, "text/csv")}, headers=admin).status_code == 422
    bad_sale = {"product_id": product_id, "sale_date": "2026-09-01", "quantity_sold": -3}
    assert c.post("/api/sales", json=bad_sale, headers=admin).status_code == 422
    assert c.put(f"/api/inventory/{product_id}", json={"quantity": "lots"}, headers=admin).status_code == 422
    first.stop()

    second = RunningApp(db_url)
    admin = second.login()
    assert second.client.get("/api/sales", headers=admin).json() == []
    assert second.client.get(f"/api/inventory/{product_id}", headers=admin).json()["quantity"] == 0
    second.stop()


def test_restart_does_not_duplicate_the_seeded_admin(db_url):
    RunningApp(db_url).stop()
    running = RunningApp(db_url)

    users = running.client.get("/api/users", headers=running.login()).json()

    assert [u["email"] for u in users].count(settings.admin_email) == 1
    running.stop()
