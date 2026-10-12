"""Unit tests for analytics/forecasting.py (TC-FCST-01, TC-FCST-02, TC-FCST-03)."""
import csv
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from app.analytics.forecasting import (
    HOLT_WINTERS,
    MODEL_VERSION,
    SIMPLE_ES,
    forecast,
)
from app.analytics.preprocessing import InsufficientHistoryError, build_series

SAMPLES = Path(__file__).resolve().parents[2] / "data" / "samples" / "sales_patterns.csv"


def rows_for(sku: str):
    with open(SAMPLES, newline="") as f:
        return [
            {"sale_date": r["date"], "quantity_sold": r["quantity_sold"]}
            for r in csv.DictReader(f)
            if r["sku"] == sku
        ]


def flat_series(periods: int, qty: float = 10, unit: str = "week"):
    rows = [
        {"sale_date": (date(2024, 1, 1) + timedelta(days=i)).isoformat(), "quantity_sold": qty}
        for i in range(periods * 7)
    ]
    return build_series(rows, unit="week")


def test_horizon_4_weeks_returns_exactly_4_points():  # TC-FCST-01
    result = forecast(flat_series(20), horizon=4, unit="week")
    assert len(result.points) == 4
    assert result.horizon == 4 and result.unit == "week"


def test_weekly_points_are_consecutive_weeks():
    series = flat_series(20)
    result = forecast(series, horizon=3, unit="week")
    last = series.index[-1].date()
    assert [p.period_start for p in result.points] == [last + timedelta(weeks=k) for k in (1, 2, 3)]


def test_monthly_forecast_points_start_on_first_of_month():
    rows = [
        {"sale_date": (date(2023, 1, 1) + timedelta(days=i)).isoformat(), "quantity_sold": 3}
        for i in range(365)
    ]
    series = build_series(rows, unit="month")
    result = forecast(series, horizon=6, unit="month")
    assert len(result.points) == 6
    assert all(p.period_start.day == 1 for p in result.points)


def test_result_carries_metadata():  # TC-FCST-03
    result = forecast(flat_series(20), horizon=2, unit="week")
    assert result.model_name in (HOLT_WINTERS, SIMPLE_ES)
    assert result.model_version == MODEL_VERSION
    assert isinstance(result.generated_at, datetime)


def test_fewer_than_8_periods_raises():  # TC-FCST-02
    short = flat_series(8).iloc[:5]
    with pytest.raises(InsufficientHistoryError):
        forecast(short, horizon=4, unit="week")


@pytest.mark.parametrize(
    "horizon,unit",
    [(0, "week"), (13, "week"), (-1, "week"), (7, "month"), (0, "month"), (4, "day")],
)
def test_invalid_horizon_or_unit_rejected(horizon, unit):
    with pytest.raises(ValueError):
        forecast(flat_series(20), horizon=horizon, unit=unit)


def test_short_history_uses_simple_exponential_smoothing():
    assert forecast(flat_series(20), 4, "week").model_name == SIMPLE_ES


def test_two_seasonal_cycles_use_holt_winters():
    series = build_series(rows_for("SKU-SEASONAL"), unit="week")  # 156 weeks >= 2 x 52
    assert forecast(series, 12, "week").model_name == HOLT_WINTERS


def test_predictions_are_never_negative():
    rows = [
        {"sale_date": (date(2024, 1, 1) + timedelta(days=i)).isoformat(),
         "quantity_sold": max(0, 100 - i // 7 * 12)}
        for i in range(70)  # steadily falling to zero
    ]
    result = forecast(build_series(rows, "week"), 8, "week")
    assert all(p.predicted_qty >= 0 for p in result.points)


def test_all_zero_demand_forecasts_zero():
    result = forecast(flat_series(20, qty=0), 4, "week")
    assert all(p.predicted_qty == 0 for p in result.points)


@pytest.mark.parametrize("sku", ["SKU-NORMAL", "SKU-INCREASING", "SKU-SEASONAL", "SKU-SPARSE"])
def test_all_sample_demand_patterns_forecast(sku):
    series = build_series(rows_for(sku), unit="week")
    result = forecast(series, 4, "week")
    assert len(result.points) == 4
    assert all(p.predicted_qty >= 0 for p in result.points)


def test_normal_demand_forecast_is_near_the_true_level():
    series = build_series(rows_for("SKU-NORMAL"), unit="week")  # ~20/day -> ~140/week
    result = forecast(series, 4, "week")
    assert all(120 < p.predicted_qty < 160 for p in result.points)
