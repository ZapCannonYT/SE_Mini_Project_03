"""Unit tests for analytics/planning.py (TC-PLAN-01, TC-PLAN-02, TC-PLAN-03)."""
from types import SimpleNamespace

import pytest

from app.analytics.planning import (
    Risk,
    classify_risk,
    demand_from_forecast,
    plan,
    reorder_qty,
)


# ---- TC-PLAN-01: reorder quantity -------------------------------------------
@pytest.mark.parametrize(
    "demand,safety,stock,expected",
    [
        (100, 20, 50, 70),        # example from the plan
        (100, 20, 0, 120),        # zero stock: order demand + safety stock
        (0, 20, 0, 20),           # zero demand: still top up to safety stock
        (0, 0, 0, 0),             # nothing needed
        (100, 20, 120, 0),        # stock exactly covers demand + safety -> 0
        (100, 20, 500, 0),        # plenty of stock -> never negative
        (10.2, 0, 0, 11),         # fractional need rounds UP
        (0.1 + 0.2, 0, 0, 1),     # 0.30000000000000004 must not break rounding
    ],
)
def test_reorder_qty(demand, safety, stock, expected):
    assert reorder_qty(demand, safety, stock) == expected


# ---- TC-PLAN-02: risk classification -----------------------------------------
@pytest.mark.parametrize(
    "stock,demand,factor,expected",
    [
        (50, 100, 1.5, Risk.STOCKOUT),     # stock below demand
        (0, 100, 1.5, Risk.STOCKOUT),      # zero stock
        (99.99, 100, 1.5, Risk.STOCKOUT),  # just under the threshold
        (100, 100, 1.5, Risk.NONE),        # exact stockout threshold is not a risk
        (120, 100, 1.5, Risk.NONE),        # comfortable
        (150, 100, 1.5, Risk.NONE),        # exact overstock threshold is not a risk
        (150.01, 100, 1.5, Risk.OVERSTOCK),  # just over the threshold
        (500, 100, 1.5, Risk.OVERSTOCK),
        (0, 0, 1.5, Risk.NONE),            # no stock, no demand
        (10, 0, 1.5, Risk.OVERSTOCK),      # stock but zero demand
        (250, 100, 2.5, Risk.NONE),        # custom factor from settings
        (251, 100, 2.5, Risk.OVERSTOCK),
    ],
)
def test_classify_risk(stock, demand, factor, expected):
    assert classify_risk(stock, demand, factor) is expected


def test_default_overstock_factor_is_1_5():
    assert classify_risk(150, 100) is Risk.NONE
    assert classify_risk(151, 100) is Risk.OVERSTOCK


# ---- TC-PLAN-03: result keeps every input used ------------------------------
def test_plan_example_from_requirements():
    result = plan(current_stock=50, forecast_demand=100, safety_stock=20)
    assert result.reorder_qty == 70
    assert result.risk is Risk.STOCKOUT


def test_plan_result_keeps_all_inputs_for_the_ui():
    result = plan(current_stock=50, forecast_demand=100, safety_stock=20, overstock_factor=2.0)
    assert result.current_stock == 50
    assert result.forecast_demand == 100
    assert result.safety_stock == 20
    assert result.overstock_factor == 2.0


def test_risk_values_match_database_strings():
    assert [r.value for r in Risk] == ["none", "stockout", "overstock"]


def test_demand_from_forecast_sums_the_points():
    points = [SimpleNamespace(predicted_qty=q) for q in (10.5, 20, 30.25)]
    assert demand_from_forecast(points) == pytest.approx(60.75)


# ---- invalid input -----------------------------------------------------------
@pytest.mark.parametrize("args", [(-1, 10, 5), (10, -1, 5), (10, 10, -5), ("a", 1, 1)])
def test_reorder_qty_rejects_bad_inputs(args):
    with pytest.raises(ValueError):
        reorder_qty(*args)


@pytest.mark.parametrize("factor", [0.5, 0, -1, "x", float("nan")])
def test_classify_risk_rejects_bad_overstock_factor(factor):
    with pytest.raises(ValueError):
        classify_risk(10, 10, factor)


def test_classify_risk_rejects_negative_stock():
    with pytest.raises(ValueError):
        classify_risk(-1, 10)
