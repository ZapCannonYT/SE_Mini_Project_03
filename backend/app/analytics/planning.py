"""Planning calculations: reorder quantity and stockout/overstock risk
(SRS DFIP-F-013, DFIP-F-014, DFIP-F-015).

Pure functions: no database or API needed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

DEFAULT_OVERSTOCK_FACTOR = 1.5


class Risk(str, Enum):
    NONE = "none"
    STOCKOUT = "stockout"
    OVERSTOCK = "overstock"


@dataclass(frozen=True)
class PlanResult:
    """Result of a planning run. Keeps every input used, so the UI can show
    them later (DFIP-F-016)."""
    current_stock: float
    forecast_demand: float
    safety_stock: float
    overstock_factor: float
    reorder_qty: int
    risk: Risk


def _check_non_negative(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a number")
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")


def demand_from_forecast(points: Iterable[Any]) -> float:
    """Total forecast demand = sum of predicted_qty over the forecast points."""
    return float(sum(p.predicted_qty for p in points))


def reorder_qty(forecast_demand: float, safety_stock: float, current_stock: float) -> int:
    """reorder_qty = max(0, ceil(forecast_demand + safety_stock - current_stock))"""
    _check_non_negative("forecast_demand", forecast_demand)
    _check_non_negative("safety_stock", safety_stock)
    _check_non_negative("current_stock", current_stock)
    needed = forecast_demand + safety_stock - current_stock
    return max(0, math.ceil(round(needed, 6)))  # round() avoids float noise like 0.30000000000000004


def classify_risk(
    current_stock: float,
    forecast_demand: float,
    overstock_factor: float = DEFAULT_OVERSTOCK_FACTOR,
) -> Risk:
    """stockout  : current_stock < forecast_demand
    overstock : current_stock > overstock_factor x forecast_demand
    none      : otherwise (exact thresholds are NOT a risk)
    """
    _check_non_negative("current_stock", current_stock)
    _check_non_negative("forecast_demand", forecast_demand)
    if isinstance(overstock_factor, bool) or not isinstance(overstock_factor, (int, float)) \
            or not math.isfinite(overstock_factor) or overstock_factor < 1:
        raise ValueError(f"overstock_factor must be a number >= 1, got {overstock_factor!r}")

    if current_stock < forecast_demand:
        return Risk.STOCKOUT
    if current_stock > overstock_factor * forecast_demand:
        return Risk.OVERSTOCK
    return Risk.NONE


def plan(
    current_stock: float,
    forecast_demand: float,
    safety_stock: float,
    overstock_factor: float = DEFAULT_OVERSTOCK_FACTOR,
) -> PlanResult:
    """Combine reorder quantity and risk into one result."""
    return PlanResult(
        current_stock=current_stock,
        forecast_demand=forecast_demand,
        safety_stock=safety_stock,
        overstock_factor=overstock_factor,
        reorder_qty=reorder_qty(forecast_demand, safety_stock, current_stock),
        risk=classify_risk(current_stock, forecast_demand, overstock_factor),
    )
