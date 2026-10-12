"""Sales data management API (DFIP-F-007 to F-009, TC-SALES-01 to 03, TC-SEC-04 partial)."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.analytics.preprocessing import build_series
from app.models import Role, SalesRecord
from app.services.sales_service import MAX_IMPORT_BYTES, get_sales_history

SAMPLES = Path(__file__).resolve().parents[2] / "data" / "samples"


@pytest.fixture
def admin(auth_headers):
    return auth_headers(Role.ADMIN)


@pytest.fixture
def products(client, admin):
    """SKU-100 and SKU-200, matching data/samples/valid_sales.csv and invalid_sales.csv."""
    ids = {}
    for sku, name in [("SKU-100", "Steel bolts"), ("SKU-200", "Copper wire")]:
        ids[sku] = client.post("/api/products", json={"sku": sku, "name": name}, headers=admin).json()["id"]
    return ids


def add(client, headers, product_id, sale_date="2026-09-01", qty=10):
    return client.post(
        "/api/sales", json={"product_id": product_id, "sale_date": sale_date, "quantity_sold": qty}, headers=headers
    )


def upload(client, headers, content: bytes | str, filename="sales.csv"):
    if isinstance(content, str):
        content = content.encode("utf-8")
    return client.post("/api/sales/import", files={"file": (filename, content, "text/csv")}, headers=headers)


def sales_count(db):
    return db.scalar(select(func.count(SalesRecord.id)))


# ---- Manual entry (TC-SALES-01) ----

def test_valid_sale_is_stored_with_product_and_date(client, admin, products):  # TC-SALES-01
    response = add(client, admin, products["SKU-100"], "2026-09-01", 12)

    assert response.status_code == 201
    body = response.json()
    assert (body["sku"], body["sale_date"], body["quantity_sold"]) == ("SKU-100", "2026-09-01", 12)
    assert body["created_by"] is not None


def test_planner_can_add_but_viewer_cannot(client, auth_headers, products):
    assert add(client, auth_headers(Role.PLANNER), products["SKU-100"]).status_code == 201
    assert add(client, auth_headers(Role.VIEWER), products["SKU-200"]).status_code == 403


def test_second_entry_for_same_product_and_date_is_rejected(client, admin, products):
    add(client, admin, products["SKU-100"], "2026-09-01")
    response = add(client, admin, products["SKU-100"], "2026-09-01", 5)

    assert response.status_code == 409
    assert response.json()["code"] == "sale_exists"


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity_sold", -1),
        ("quantity_sold", "abc"),
        ("quantity_sold", 2.5),
        ("sale_date", "01/09/2026"),
        ("sale_date", "2026-02-30"),
        ("sale_date", 0),
        ("sale_date", (date.today() + timedelta(days=1)).isoformat()),
        ("product_id", "SKU-100"),
    ],
)
def test_invalid_sale_fields_are_rejected(client, admin, products, field, value):
    payload = {"product_id": products["SKU-100"], "sale_date": "2026-09-01", "quantity_sold": 3, field: value}
    response = client.post("/api/sales", json=payload, headers=admin)

    assert response.status_code == 422
    assert response.json()["details"][0]["field"] == field


def test_unknown_or_deactivated_product_is_rejected(client, admin, products):
    assert add(client, admin, 999).json()["code"] == "product_not_found"

    client.patch(f"/api/products/{products['SKU-200']}/deactivate", headers=admin)
    response = add(client, admin, products["SKU-200"])
    assert response.status_code == 409
    assert response.json()["code"] == "product_inactive"


def test_sales_endpoints_need_a_token(client):
    assert client.get("/api/sales").status_code == 401
    assert client.post("/api/sales", json={}).status_code == 401
    assert upload(client, {}, "sku,date,quantity_sold\n").status_code == 401


# ---- View and filter (TC-SALES-03) ----

def test_filter_by_product_and_date_range(client, admin, auth_headers, products):  # TC-SALES-03
    for day in ("2026-09-01", "2026-09-05", "2026-09-10"):
        add(client, admin, products["SKU-100"], day)
        add(client, admin, products["SKU-200"], day)

    response = client.get(
        "/api/sales",
        params={"product_id": products["SKU-100"], "from": "2026-09-02", "to": "2026-09-10"},
        headers=auth_headers(Role.VIEWER),
    )

    assert response.status_code == 200
    assert [(r["sku"], r["sale_date"]) for r in response.json()] == [
        ("SKU-100", "2026-09-05"),
        ("SKU-100", "2026-09-10"),
    ]


def test_list_without_filters_returns_everything_oldest_first(client, admin, products):
    add(client, admin, products["SKU-200"], "2026-09-03")
    add(client, admin, products["SKU-100"], "2026-09-01")

    dates = [r["sale_date"] for r in client.get("/api/sales", headers=admin).json()]
    assert dates == ["2026-09-01", "2026-09-03"]


def test_from_after_to_is_rejected(client, admin):
    response = client.get("/api/sales", params={"from": "2026-09-10", "to": "2026-09-01"}, headers=admin)
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_date_range"


# ---- CSV import (TC-SALES-02) ----

def test_valid_sample_csv_imports_every_row(client, admin, products, db):  # TC-SALES-02 (valid file)
    response = upload(client, admin, (SAMPLES / "valid_sales.csv").read_bytes())

    assert response.status_code == 200
    assert response.json() == {"total_rows": 20, "imported": 20, "rejected": 0, "errors": []}
    assert sales_count(db) == 20


def test_invalid_sample_csv_imports_valid_rows_and_reports_the_rest(client, admin, products, db):  # TC-SALES-02
    add(client, admin, products["SKU-200"], "2026-07-01", 99)  # existing data must stay untouched

    result = upload(client, admin, (SAMPLES / "invalid_sales.csv").read_bytes()).json()

    assert (result["total_rows"], result["imported"], result["rejected"]) == (10, 2, 8)
    errors = {e["row"]: e["error"] for e in result["errors"]}
    assert sorted(errors) == [3, 4, 5, 6, 7, 8, 9, 10]
    assert "Invalid quantity '-4'" in errors[3]
    assert "Invalid quantity 'abc'" in errors[4]
    assert "Invalid date '01/08/2026'" in errors[5]
    assert "Unknown SKU 'SKU-999'" in errors[6]
    assert "Duplicate of an earlier row" in errors[7]
    assert "Invalid quantity '3.5'" in errors[8]
    assert "in the future" in errors[9]
    assert "SKU is empty" in errors[10]

    assert sales_count(db) == 3  # 1 existing + 2 imported
    existing = client.get("/api/sales", params={"from": "2026-07-01", "to": "2026-07-01"}, headers=admin).json()
    assert existing[0]["quantity_sold"] == 99


def test_rows_already_stored_are_reported_not_overwritten(client, admin, products):
    add(client, admin, products["SKU-100"], "2026-09-01", 50)

    result = upload(client, admin, "sku,date,quantity_sold\nSKU-100,2026-09-01,1\n").json()

    assert result["imported"] == 0
    assert "already recorded" in result["errors"][0]["error"]
    assert client.get("/api/sales", headers=admin).json()[0]["quantity_sold"] == 50


def test_header_is_flexible_and_sku_is_case_insensitive(client, admin, products):
    csv_text = "﻿ Quantity_Sold , SKU ,Date,notes\n5,sku-100,2026-09-01,promo\n"  # BOM, spaces, order, extra column
    result = upload(client, admin, csv_text).json()
    assert result["imported"] == 1


def test_blank_lines_are_skipped(client, admin, products):
    result = upload(client, admin, "sku,date,quantity_sold\n\nSKU-100,2026-09-01,4\n,,\n").json()
    assert (result["total_rows"], result["imported"]) == (1, 1)


@pytest.mark.parametrize(
    "content,message",
    [
        ("", "empty"),
        ("sku,date\nSKU-100,2026-09-01\n", "Missing column(s): quantity_sold"),
        ("sku,date,quantity_sold\n", "no data rows"),
        (b"\xff\xfe\x00bad", "UTF-8"),
    ],
)
def test_bad_files_are_rejected_with_400(client, admin, content, message):
    response = upload(client, admin, content)
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_csv_format"
    assert message in response.json()["message"]


def test_file_over_2mb_is_rejected_with_413(client, admin):
    big = "sku,date,quantity_sold\n" + "x" * MAX_IMPORT_BYTES
    response = upload(client, admin, big)
    assert response.status_code == 413
    assert response.json()["code"] == "file_too_large"


def test_viewer_cannot_import(client, auth_headers, products):
    response = upload(client, auth_headers(Role.VIEWER), (SAMPLES / "valid_sales.csv").read_bytes())
    assert response.status_code == 403


def test_sql_like_input_is_treated_as_plain_text(client, admin, products, db):  # TC-SEC-04 (partial)
    csv_text = "sku,date,quantity_sold\n\"SKU-100'; DROP TABLE sales_records;--\",2026-09-01,1\n"
    result = upload(client, admin, csv_text).json()

    assert result["imported"] == 0
    assert "Unknown SKU" in result["errors"][0]["error"]
    assert sales_count(db) == 0  # table still there and queryable


# ---- Hand-off to forecasting ----

def test_imported_history_feeds_the_forecasting_preprocessor(client, admin, db):
    skus = ["SKU-NORMAL", "SKU-INCREASING", "SKU-SEASONAL", "SKU-SPARSE"]
    ids = {s: client.post("/api/products", json={"sku": s, "name": s}, headers=admin).json()["id"] for s in skus}

    result = upload(client, admin, (SAMPLES / "sales_patterns.csv").read_bytes()).json()
    assert result["rejected"] == 0 and result["imported"] == result["total_rows"]

    history = get_sales_history(db, ids["SKU-SEASONAL"])
    assert history == sorted(history, key=lambda r: r["sale_date"])
    assert len(build_series(history, unit="week")) >= 104  # enough for Holt-Winters
