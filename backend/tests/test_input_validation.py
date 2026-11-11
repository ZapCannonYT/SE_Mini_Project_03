"""TC-SEC-04 (DFIP-SR-004): malformed and script/SQL-like input is rejected or stored safely as plain text."""
import pytest

from app.models import Product, Role, SalesRecord, User

SCRIPT = "<script>alert('x')</script>"
SQL = "Robert'); DROP TABLE products;--"
SQL_OR = "' OR '1'='1"


@pytest.fixture
def admin(auth_headers):
    return auth_headers(Role.ADMIN)


@pytest.fixture
def product_id(client, admin):
    return client.post("/api/products", json={"sku": "SKU-100", "name": "Bolts"}, headers=admin).json()["id"]


@pytest.mark.parametrize("text", [SCRIPT, SQL, SQL_OR, "Écrou 10 mm ✓", "a; DELETE FROM users"])
def test_free_text_is_stored_verbatim_and_returned_as_json(client, admin, db, text):  # TC-SEC-04
    response = client.post(
        "/api/products", json={"sku": "SKU-1", "name": text, "category": text}, headers=admin
    )

    assert response.status_code == 201
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["name"] == text
    assert db.query(Product).one().category == text
    # The tables the string tries to drop or empty are untouched.
    assert db.query(User).count() >= 1
    assert client.get("/api/products", headers=admin).status_code == 200


@pytest.mark.parametrize("sku", [SCRIPT, SQL, SQL_OR, "SKU 100", "-SKU", "x" * 51, ""])
def test_sku_outside_the_allowed_pattern_is_rejected(client, admin, db, sku):  # TC-SEC-04
    response = client.post("/api/products", json={"sku": sku, "name": "Bolts"}, headers=admin)

    assert response.status_code == 422
    assert {d["field"] for d in response.json()["details"]} == {"sku"}
    assert db.query(Product).count() == 0


@pytest.mark.parametrize(
    "params",
    [
        {"product_id": "1 OR 1=1"},
        {"product_id": "1; DROP TABLE sales_records"},
        {"start_date": f"2026-01-01{SQL_OR}"},
        {"end_date": SCRIPT},
    ],
)
def test_injection_in_query_filters_is_rejected(client, admin, params):  # TC-SEC-04
    response = client.get("/api/sales", params=params, headers=admin)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


@pytest.mark.parametrize("path", ["/api/products/1%20OR%201=1", "/api/inventory/1;DROP", "/api/products/-1abc"])
def test_injection_in_path_ids_is_rejected(client, admin, path):  # TC-SEC-04
    assert client.get(path, headers=admin).status_code == 422


@pytest.mark.parametrize("email", [SQL_OR, f"admin@dfip.local{SQL_OR}", "admin@dfip.local' --"])
def test_sql_like_login_does_not_log_in(client, email):  # TC-SEC-04
    response = client.post("/api/auth/login", json={"email": email, "password": SQL_OR})

    assert response.status_code == 401
    assert "access_token" not in response.json()


def test_csv_with_script_sql_and_formula_values_is_rejected_row_by_row(client, admin, product_id, db):  # TC-SEC-04
    csv = (
        "sku,date,quantity_sold\n"
        f"SKU-100{SQL_OR},2026-09-01,4\n"
        "=HYPERLINK(\"http://evil\"),2026-09-01,4\n"
        f"{SCRIPT},2026-09-01,4\n"
        "SKU-100,2026-09-01;DROP TABLE sales_records,4\n"
        "SKU-100,2026-09-01,4; DELETE FROM sales_records\n"
        "SKU-100,2026-09-01,1e3\n"
        "SKU-100,2026-09-02,5\n"
    )
    response = client.post("/api/sales/import", files={"file": ("s.csv", csv.encode(), "text/csv")}, headers=admin)

    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 1
    assert [r["row"] for r in body["rejected"]] == [2, 3, 4, 5, 6, 7]
    assert db.query(SalesRecord).count() == 1


@pytest.mark.parametrize(
    "body",
    [b"not json", b"[1, 2, 3]", b'{"product_id": 1, "sale_date": "2026-09-01"', b"null"],
)
def test_malformed_json_body_is_rejected(client, admin, product_id, db, body):  # TC-SEC-04
    headers = {**admin, "Content-Type": "application/json"}
    response = client.post("/api/sales", content=body, headers=headers)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert db.query(SalesRecord).count() == 0


def test_oversized_text_is_rejected(client, admin, db):  # TC-SEC-04
    response = client.post("/api/products", json={"sku": "SKU-1", "name": "x" * 201}, headers=admin)

    assert response.status_code == 422
    assert db.query(Product).count() == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"name": SCRIPT, "email": "a@dfip.local", "password": "Password1!", "role": "admin' OR '1'='1"},
        {"name": "A", "email": SQL_OR, "password": "Password1!", "role": "viewer"},
        {"name": "A", "email": "a@dfip.local", "password": "Password1!", "role": "viewer", "is_admin": True},
    ],
)
def test_user_admin_rejects_malformed_or_extra_fields(client, admin, db, payload):  # TC-SEC-04
    before = db.query(User).count()

    response = client.post("/api/users", json=payload, headers=admin)

    assert response.status_code == 422
    assert db.query(User).count() == before


def test_error_responses_do_not_leak_internals(client, admin):  # TC-SEC-04
    response = client.get("/api/sales", params={"product_id": SQL}, headers=admin)

    text = response.text.lower()
    assert "traceback" not in text
    assert "sqlalchemy" not in text
    assert "select " not in text
