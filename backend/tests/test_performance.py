"""Response-time checks for TC-PERF-01 and TC-PERF-02 (DFIP-NF-001/002)."""
from datetime import date, timedelta
from math import ceil
from time import perf_counter

import pytest
from app.models import Inventory, Product, Role, SalesRecord

LIST_AND_DASHBOARD_LIMIT_SECONDS = 3.0
FORECAST_LIMIT_SECONDS = 10.0
READ_SAMPLE_COUNT = 30


def seed_read_dataset(db) -> tuple[list[Product], Product]:
    """Seed a small academic-scale catalogue with history for each product."""
    today = date.today()
    current_week = today - timedelta(days=today.weekday())
    products = [
        Product(
            sku=f"PERF-{index:03d}",
            name=f"Performance sample {index}",
            safety_stock=12,
            overstock_factor=1.5,
            inventory=Inventory(quantity=80 + index),
        )
        for index in range(1, 13)
    ]
    forecast_product = Product(
        sku="PERF-FORECAST",
        name="104-week forecast sample",
        safety_stock=20,
        overstock_factor=1.5,
        inventory=Inventory(quantity=150),
    )
    db.add_all([*products, forecast_product])
    db.flush()

    sales = []
    for product_index, product in enumerate(products):
        first_week = current_week - timedelta(weeks=55)
        for week in range(56):
            # Rotate through stable, increasing, seasonal and sparse demand shapes.
            if product_index % 4 == 0:
                quantity = 20
            elif product_index % 4 == 1:
                quantity = 10 + week
            elif product_index % 4 == 2:
                quantity = 18 + (week % 13) * 2
            else:
                quantity = 0 if week % 4 else 35
            sales.append(
                SalesRecord(
                    product_id=product.id,
                    sale_date=first_week + timedelta(weeks=week),
                    quantity_sold=quantity,
                )
            )

    first_forecast_week = current_week - timedelta(weeks=103)
    for week in range(104):
        # A repeating annual shape exercises the seasonal forecasting path.
        quantity = 25 + (week % 52) // 4 + (week % 7)
        sales.append(
            SalesRecord(
                product_id=forecast_product.id,
                sale_date=first_forecast_week + timedelta(weeks=week),
                quantity_sold=quantity,
            )
        )

    db.add_all(sales)
    db.commit()
    return products, forecast_product


def p90(values: list[float]) -> float:
    """Nearest-rank 90th percentile, matching the STP's 90% threshold."""
    return sorted(values)[ceil(0.90 * len(values)) - 1]


@pytest.mark.parametrize(
    "name,path",
    [
        ("products", "/api/products"),
        ("inventory", "/api/inventory"),
        ("sales", "/api/sales"),
        ("dashboard", "/api/dashboard"),
    ],
)
def test_list_and_dashboard_requests_meet_p90_target(
    client, db, auth_headers, name, path
):  # TC-PERF-01
    """Measure representative list/dashboard reads after warming the API route."""
    seed_read_dataset(db)
    headers = auth_headers(Role.VIEWER)

    for _ in range(2):
        response = client.get(path, headers=headers)
        assert response.status_code == 200, response.text

    durations = []
    for _ in range(READ_SAMPLE_COUNT):
        started = perf_counter()
        response = client.get(path, headers=headers)
        durations.append(perf_counter() - started)
        assert response.status_code == 200, response.text

    median_seconds = sorted(durations)[len(durations) // 2]
    p90_seconds = p90(durations)
    max_seconds = max(durations)
    print(
        f"TC-PERF-01 {name}: n={READ_SAMPLE_COUNT}, "
        f"median={median_seconds * 1000:.3f} ms, "
        f"p90={p90_seconds * 1000:.3f} ms, max={max_seconds * 1000:.3f} ms"
    )

    assert p90_seconds < LIST_AND_DASHBOARD_LIMIT_SECONDS, (
        f"{name} p90 was {p90_seconds:.3f}s; "
        f"target is under {LIST_AND_DASHBOARD_LIMIT_SECONDS:.1f}s"
    )


def test_single_product_forecast_meets_ten_second_target(client, db, auth_headers):  # TC-PERF-02
    """Measure one 12-week forecast using 104 weekly observations."""
    _, product = seed_read_dataset(db)
    headers = auth_headers(Role.PLANNER)

    started = perf_counter()
    response = client.post(
        "/api/forecasts",
        json={"product_id": product.id, "horizon": 12, "unit": "week"},
        headers=headers,
    )
    elapsed_seconds = perf_counter() - started

    assert response.status_code == 201, response.text
    assert len(response.json()["points"]) == 12
    print(f"TC-PERF-02 forecast: history=104 weeks, elapsed={elapsed_seconds * 1000:.3f} ms")

    assert elapsed_seconds < FORECAST_LIMIT_SECONDS, (
        f"forecast took {elapsed_seconds:.3f}s; target is under {FORECAST_LIMIT_SECONDS:.1f}s"
    )
