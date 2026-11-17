"""TC-RPT-01 / TC-RPT-02 (DFIP-F-019, F-020): planning report filters and CSV export."""
import csv
import io
from datetime import UTC, date, datetime

from app.models import Forecast, ForecastPoint, HorizonUnit, Product, Recommendation, RiskLevel, Role


def add_rec(db, sku, created, risk=RiskLevel.STOCKOUT, name=None, reorder=10):
    product = db.query(Product).filter_by(sku=sku).first()
    if product is None:
        product = Product(sku=sku, name=name or f"Item {sku}", safety_stock=5, overstock_factor=1.5)
        db.add(product)
        db.flush()
    forecast = Forecast(
        product_id=product.id,
        horizon=2,
        unit=HorizonUnit.WEEK,
        model_name="m",
        model_version="1",
        generated_at=created,
    )
    forecast.points = [ForecastPoint(period_start=date(2025, 1, 6), predicted_qty=5)]
    db.add(forecast)
    db.flush()
    rec = Recommendation(
        product_id=product.id,
        forecast_id=forecast.id,
        current_stock=3,
        forecast_demand=20.5,
        safety_stock=5,
        overstock_factor=1.5,
        reorder_qty=reorder,
        risk=risk,
        created_at=created,
    )
    db.add(rec)
    db.commit()
    return product.id, rec.id


def seed(db):
    a, _ = add_rec(db, "A-1", datetime(2025, 3, 1, 10, tzinfo=UTC), RiskLevel.STOCKOUT)
    b, _ = add_rec(db, "B-1", datetime(2025, 3, 5, 10, tzinfo=UTC), RiskLevel.OVERSTOCK)
    add_rec(db, "A-1", datetime(2025, 3, 9, 23, 30, tzinfo=UTC), RiskLevel.NONE, reorder=0)
    return a, b


def get(client, headers, path="/api/reports/planning", **params):
    return client.get(path, params=params, headers=headers)


def test_report_lists_rows_newest_first_with_all_inputs(client, db, auth_headers):
    seed(db)
    res = get(client, auth_headers(Role.VIEWER))
    assert res.status_code == 200
    rows = res.json()
    assert [r["created_at"][:10] for r in rows] == ["2025-03-09", "2025-03-05", "2025-03-01"]
    first = rows[0]
    for key in ("sku", "name", "horizon", "unit", "current_stock", "forecast_demand", "safety_stock",
                "overstock_factor", "reorder_qty", "risk", "forecast_id", "recommendation_id"):
        assert key in first


def test_report_filters_by_product(client, db, auth_headers):
    a, _b = seed(db)
    rows = get(client, auth_headers(Role.PLANNER), product_id=a).json()
    assert len(rows) == 2 and {r["sku"] for r in rows} == {"A-1"}


def test_report_filters_by_inclusive_date_range(client, db, auth_headers):
    seed(db)
    h = auth_headers(Role.PLANNER)
    assert len(get(client, h, start_date="2025-03-05").json()) == 2
    assert len(get(client, h, end_date="2025-03-05").json()) == 2
    assert [r["created_at"][:10] for r in get(client, h, start_date="2025-03-05", end_date="2025-03-05").json()] == [
        "2025-03-05"
    ]
    # An end date includes records created late that day.
    assert len(get(client, h, end_date="2025-03-09").json()) == 3


def test_report_filters_by_risk(client, db, auth_headers):
    seed(db)
    rows = get(client, auth_headers(Role.VIEWER), risk="overstock").json()
    assert [r["sku"] for r in rows] == ["B-1"]


def test_report_rejects_reversed_dates_and_bad_values(client, db, auth_headers):
    h = auth_headers(Role.VIEWER)
    res = get(client, h, start_date="2025-03-09", end_date="2025-03-01")
    assert res.status_code == 422 and res.json()["code"] == "validation_error"
    assert get(client, h, risk="bogus").status_code == 422
    assert get(client, h, product_id=0).status_code == 422


def test_report_requires_login(client):
    assert client.get("/api/reports/planning").status_code == 401
    assert client.get("/api/reports/planning/export").status_code == 401


def test_empty_report_is_an_empty_list(client, auth_headers):
    assert get(client, auth_headers(Role.VIEWER)).json() == []


def parse_csv(text):
    return list(csv.DictReader(io.StringIO(text)))


def test_csv_export_has_same_rows_as_the_report(client, db, auth_headers):
    a, _b = seed(db)
    h = auth_headers(Role.VIEWER)
    table = get(client, h, product_id=a, start_date="2025-03-01", end_date="2025-03-31").json()
    res = get(client, h, path="/api/reports/planning/export", product_id=a,
              start_date="2025-03-01", end_date="2025-03-31")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "planning_report.csv" in res.headers["content-disposition"]
    rows = parse_csv(res.text)
    assert len(rows) == len(table) == 2
    for csv_row, api_row in zip(rows, table, strict=True):
        assert csv_row["recommendation_id"] == str(api_row["recommendation_id"])
        assert csv_row["sku"] == api_row["sku"]
        assert csv_row["reorder_qty"] == str(api_row["reorder_qty"])
        assert csv_row["risk"] == api_row["risk"]
        assert float(csv_row["forecast_demand"]) == api_row["forecast_demand"]


def test_csv_export_with_no_rows_is_header_only(client, auth_headers):
    res = get(client, auth_headers(Role.VIEWER), path="/api/reports/planning/export")
    lines = res.text.strip().splitlines()
    assert len(lines) == 1 and lines[0].startswith("recommendation_id,sku,name")


def test_csv_neutralises_spreadsheet_formulas(client, db, auth_headers):
    add_rec(db, "F-1", datetime(2025, 3, 1, tzinfo=UTC), name="=HYPERLINK(\"http://evil\")")
    res = get(client, auth_headers(Role.VIEWER), path="/api/reports/planning/export")
    assert parse_csv(res.text)[0]["name"].startswith("'=")


def test_forecast_demand_is_rounded_so_table_and_csv_agree(client, db, auth_headers):
    pid, _ = add_rec(db, "R-1", datetime(2025, 3, 1, tzinfo=UTC))
    rec = db.query(Recommendation).filter_by(product_id=pid).first()
    rec.forecast_demand = 478.91999999999996
    db.commit()
    h = auth_headers(Role.VIEWER)
    assert get(client, h).json()[0]["forecast_demand"] == 478.92
    assert parse_csv(get(client, h, path="/api/reports/planning/export").text)[0]["forecast_demand"] == "478.92"
