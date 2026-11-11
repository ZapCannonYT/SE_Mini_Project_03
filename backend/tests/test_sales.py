from datetime import date, timedelta
from pathlib import Path

import pytest

from app.models import Role, SalesRecord
from app.services.sales_service import get_sales_history

SAMPLES = Path(__file__).resolve().parents[2] / "data" / "samples"


@pytest.fixture
def admin(auth_headers):
    return auth_headers(Role.ADMIN)


@pytest.fixture
def planner(auth_headers):
    return auth_headers(Role.PLANNER)


@pytest.fixture
def products(client, admin):
    """SKU-100 and SKU-200, as used by the sample CSV files; returns {sku: id}."""
    ids = {}
    for sku, name in (("SKU-100", "Steel bolts"), ("SKU-200", "Copper wire")):
        response = client.post("/api/products", json={"sku": sku, "name": name}, headers=admin)
        ids[sku] = response.json()["id"]
    return ids


def add(client, headers, product_id, sale_date="2026-09-01", quantity_sold=12):
    return client.post(
        "/api/sales",
        json={"product_id": product_id, "sale_date": sale_date, "quantity_sold": quantity_sold},
        headers=headers,
    )


def upload(client, headers, content: bytes | str, filename="sales.csv"):
    if isinstance(content, str):
        content = content.encode()
    return client.post("/api/sales/import", files={"file": (filename, content, "text/csv")}, headers=headers)


def fields(response) -> set[str]:
    return {d["field"] for d in response.json()["details"]}


# TC-SALES-01: manual entry


def test_planner_records_a_sale(client, products, planner):  # TC-SALES-01
    response = add(client, planner, products["SKU-100"])

    assert response.status_code == 201
    body = response.json()
    assert body["sku"] == "SKU-100"
    assert body["name"] == "Steel bolts"
    assert body["sale_date"] == "2026-09-01"
    assert body["quantity_sold"] == 12
    assert body["created_by"] is not None


def test_second_sale_for_same_product_and_date_is_rejected(client, products, planner):  # TC-SALES-01
    add(client, planner, products["SKU-100"])
    response = add(client, planner, products["SKU-100"], quantity_sold=5)

    assert response.status_code == 409
    assert response.json()["code"] == "sale_exists"


@pytest.mark.parametrize(
    "field, value",
    [
        ("quantity_sold", -1),
        ("quantity_sold", "abc"),
        ("quantity_sold", "12"),
        ("quantity_sold", 1.5),
        ("sale_date", "01/09/2026"),
        ("sale_date", "2026-02-30"),
        ("sale_date", 20260901),
        ("sale_date", (date.today() + timedelta(days=1)).isoformat()),
        ("product_id", "1"),
    ],
)
def test_invalid_sale_is_rejected_and_nothing_stored(client, products, planner, db, field, value):  # TC-SALES-01
    payload = {"product_id": products["SKU-100"], "sale_date": "2026-09-01", "quantity_sold": 12, field: value}
    response = client.post("/api/sales", json=payload, headers=planner)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert fields(response) == {field}
    assert db.query(SalesRecord).count() == 0


def test_missing_and_unknown_fields_are_rejected(client, planner):
    response = client.post("/api/sales", json={"quantity": 3}, headers=planner)

    assert response.status_code == 422
    assert fields(response) == {"product_id", "sale_date", "quantity_sold", "quantity"}


def test_today_is_allowed(client, products, planner):
    assert add(client, planner, products["SKU-100"], sale_date=date.today().isoformat()).status_code == 201


def test_unknown_product_returns_404(client, products, planner):
    response = add(client, planner, 9999)

    assert response.status_code == 404
    assert response.json()["code"] == "product_not_found"


def test_deactivated_product_cannot_get_new_sales(client, products, admin, planner):
    client.patch(f"/api/products/{products['SKU-100']}/deactivate", headers=admin)

    response = add(client, planner, products["SKU-100"])

    assert response.status_code == 409
    assert response.json()["code"] == "product_inactive"


@pytest.mark.parametrize("role, expected", [(Role.ADMIN, 201), (Role.PLANNER, 201), (Role.VIEWER, 403)])
def test_only_admin_and_planner_can_add(client, products, auth_headers, role, expected):  # DFIP-SR-004
    assert add(client, auth_headers(role), products["SKU-100"]).status_code == expected


def test_requests_without_token_are_rejected(client):
    assert client.get("/api/sales").status_code == 401
    assert client.post("/api/sales", json={}).status_code == 401
    assert upload(client, {}, "sku,date,quantity_sold\n").status_code == 401


# TC-SALES-03: view and filter


@pytest.fixture
def six_sales(client, products, planner):
    for sku in ("SKU-100", "SKU-200"):
        for day in ("2026-09-01", "2026-09-05", "2026-09-10"):
            add(client, planner, products[sku], sale_date=day)


def test_filter_by_product_and_date_range(client, products, six_sales, auth_headers):  # TC-SALES-03
    response = client.get(
        "/api/sales",
        params={"product_id": products["SKU-100"], "start_date": "2026-09-02", "end_date": "2026-09-10"},
        headers=auth_headers(Role.VIEWER),
    )

    assert response.status_code == 200
    assert [(r["sku"], r["sale_date"]) for r in response.json()] == [
        ("SKU-100", "2026-09-10"),
        ("SKU-100", "2026-09-05"),
    ]


def test_list_without_filters_returns_everything_newest_first(client, six_sales, auth_headers):  # TC-SALES-03
    rows = client.get("/api/sales", headers=auth_headers(Role.VIEWER)).json()

    assert len(rows) == 6
    dates = [r["sale_date"] for r in rows]
    assert dates == sorted(dates, reverse=True)
    assert set(rows[0]) >= {"id", "product_id", "sku", "name", "sale_date", "quantity_sold"}


def test_range_boundaries_are_inclusive(client, six_sales, admin):
    rows = client.get("/api/sales", params={"start_date": "2026-09-05", "end_date": "2026-09-05"}, headers=admin)

    assert [r["sale_date"] for r in rows.json()] == ["2026-09-05", "2026-09-05"]


def test_start_after_end_is_rejected(client, six_sales, admin):  # TC-SALES-03
    response = client.get("/api/sales", params={"start_date": "2026-09-10", "end_date": "2026-09-01"}, headers=admin)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert fields(response) == {"start_date"}


@pytest.mark.parametrize("param", ["start_date", "end_date", "product_id"])
def test_malformed_filter_is_rejected(client, admin, param):
    response = client.get("/api/sales", params={param: "not-valid"}, headers=admin)

    assert response.status_code == 422
    assert fields(response) == {param}


# TC-SALES-02: CSV import


def test_valid_sample_file_imports_every_row(client, products, planner):  # TC-SALES-02
    response = upload(client, planner, (SAMPLES / "valid_sales.csv").read_bytes())

    assert response.status_code == 200
    assert response.json() == {"imported": 20, "rejected": []}
    assert len(client.get("/api/sales", headers=planner).json()) == 20


def test_invalid_sample_file_saves_valid_rows_and_reports_the_rest(client, products, planner):  # TC-SALES-02
    response = upload(client, planner, (SAMPLES / "invalid_sales.csv").read_bytes())

    assert response.status_code == 200
    body = response.json()
    assert body["imported"] == 2
    assert {r["row"]: r["message"] for r in body["rejected"]} == {
        3: "Quantity sold cannot be negative",
        4: "Quantity sold must be a whole number",
        5: "Date must be in YYYY-MM-DD format",
        6: "Unknown SKU: SKU-999",
        7: "Duplicate product and date in this file",
        8: "Quantity sold must be a whole number",
        9: "Date cannot be in the future",
        10: "SKU is empty",
    }
    stored = client.get("/api/sales", headers=planner).json()
    assert {(r["sku"], r["sale_date"], r["quantity_sold"]) for r in stored} == {
        ("SKU-100", "2026-08-01", 12),
        ("SKU-200", "2026-08-05", 8),
    }


def test_rows_already_stored_are_rejected(client, products, planner):
    add(client, planner, products["SKU-100"], sale_date="2026-09-01")

    body = upload(client, planner, "sku,date,quantity_sold\nsku-100,2026-09-01,4\nSKU-100,2026-09-02,4\n").json()

    assert body["imported"] == 1
    assert body["rejected"] == [{"row": 2, "message": "A sales record already exists for this product and date"}]


def test_deactivated_product_and_wrong_column_count_are_rejected(client, products, admin, planner):
    client.patch(f"/api/products/{products['SKU-200']}/deactivate", headers=admin)

    body = upload(client, planner, "sku,date,quantity_sold\nSKU-200,2026-09-01,4\nSKU-100,2026-09-01\n").json()

    assert body["imported"] == 0
    assert body["rejected"] == [
        {"row": 2, "message": "Product SKU-200 is deactivated"},
        {"row": 3, "message": "Expected 3 columns: sku,date,quantity_sold"},
    ]


def test_header_is_case_insensitive_and_excel_bom_and_blank_lines_are_ignored(client, products, planner):
    content = "﻿SKU, Date ,Quantity_Sold\r\nSKU-100,2026-09-01,4\r\n\r\nSKU-200,2026-09-01,6\r\n".encode()

    assert upload(client, planner, content).json() == {"imported": 2, "rejected": []}


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"  \n\n",
        b"product,date,qty\nSKU-100,2026-09-01,4\n",
        b"date,sku,quantity_sold\n2026-09-01,SKU-100,4\n",
        b"sku,date,quantity_sold,notes\nSKU-100,2026-09-01,4,x\n",
        "sku,date,quantity_sold\nSKU-100,2026-09-01,4\n".encode("utf-16"),
    ],
)
def test_unreadable_file_is_rejected_and_nothing_stored(client, products, planner, db, content):  # TC-SALES-02
    response = upload(client, planner, content)

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_csv"
    assert db.query(SalesRecord).count() == 0


def test_header_only_file_imports_nothing(client, planner):
    assert upload(client, planner, "sku,date,quantity_sold\n").json() == {"imported": 0, "rejected": []}


def test_file_over_2_mb_is_rejected(client, planner):
    response = upload(client, planner, b"sku,date,quantity_sold\n" + b"x" * (2 * 1024 * 1024))

    assert response.status_code == 413
    assert response.json()["code"] == "file_too_large"


def test_viewer_cannot_import(client, products, auth_headers):  # DFIP-SR-004
    response = upload(client, auth_headers(Role.VIEWER), (SAMPLES / "valid_sales.csv").read_bytes())

    assert response.status_code == 403


def test_imported_rows_record_who_imported_them(client, products, planner, db):
    upload(client, planner, "sku,date,quantity_sold\nSKU-100,2026-09-01,4\n")

    assert db.query(SalesRecord).one().created_by is not None


# History used by the forecasting API (#33)


def test_sales_history_is_oldest_first_for_one_product(client, products, six_sales, db):
    history = get_sales_history(db, products["SKU-100"])

    assert history == [
        {"sale_date": date(2026, 9, 1), "quantity_sold": 12},
        {"sale_date": date(2026, 9, 5), "quantity_sold": 12},
        {"sale_date": date(2026, 9, 10), "quantity_sold": 12},
    ]
