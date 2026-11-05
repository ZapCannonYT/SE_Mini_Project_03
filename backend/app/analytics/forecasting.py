"""Demand forecasting engine (SRS DFIP-F-010..012, DFIP-NF-002).

Holt-Winters exponential smoothing when the history covers at least two full
seasonal cycles; simple exponential smoothing otherwise. Pure functions: no
database or API needed.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

from app.analytics.preprocessing import MIN_PERIODS, VALID_UNITS, InsufficientHistoryError

MODEL_VERSION = "1.0"
HOLT_WINTERS = "Holt-Winters exponential smoothing"
SIMPLE_ES = "Simple exponential smoothing"

SEASON_LENGTH = {"week": 52, "month": 12}   # periods in one seasonal cycle
MAX_HORIZON = {"week": 12, "month": 6}      # allowed horizon: 1..MAX
_FREQ = {"week": "7D", "month": "MS"}


@dataclass(frozen=True)
class ForecastPoint:
    period_start: date
    predicted_qty: float


@dataclass(frozen=True)
class ForecastResult:
    points: list[ForecastPoint]
    model_name: str
    model_version: str
    generated_at: datetime
    unit: str
    horizon: int


def validate_horizon(horizon: int, unit: str) -> None:
    if unit not in VALID_UNITS:
        raise ValueError(f"unit must be one of {VALID_UNITS}, got {unit!r}")
    if isinstance(horizon, bool) or not isinstance(horizon, int):
        raise ValueError("horizon must be a whole number")
    if not 1 <= horizon <= MAX_HORIZON[unit]:
        raise ValueError(
            f"horizon for '{unit}' must be between 1 and {MAX_HORIZON[unit]}, got {horizon}"
        )


def _fit_holt_winters(values: pd.Series, horizon: int, unit: str) -> np.ndarray | None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = ExponentialSmoothing(
                values, trend="add", damped_trend=True, seasonal="add",
                seasonal_periods=SEASON_LENGTH[unit], initialization_method="estimated",
            ).fit()
            pred = np.asarray(fit.forecast(horizon), dtype=float)
    except Exception:
        return None
    return pred if np.all(np.isfinite(pred)) else None


def _fit_simple(values: pd.Series, horizon: int) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = SimpleExpSmoothing(values, initialization_method="estimated").fit()
        pred = np.asarray(fit.forecast(horizon), dtype=float)
    if not np.all(np.isfinite(pred)):
        pred = np.full(horizon, float(values.mean()))
    return pred


def forecast(series: pd.Series, horizon: int, unit: str) -> ForecastResult:
    """Forecast `horizon` future periods from a weekly/monthly demand series."""
    validate_horizon(horizon, unit)
    if len(series) < MIN_PERIODS:
        raise InsufficientHistoryError(
            f"Need at least {MIN_PERIODS} {unit}s of history, got {len(series)}."
        )

    values = series.astype(float).copy()
    values.index = pd.DatetimeIndex(values.index, freq=_FREQ[unit])

    pred = None
    model_name = SIMPLE_ES
    if values.abs().sum() == 0:
        pred = np.zeros(horizon)
    else:
        if len(values) >= 2 * SEASON_LENGTH[unit]:
            pred = _fit_holt_winters(values, horizon, unit)
            if pred is not None:
                model_name = HOLT_WINTERS
        if pred is None:
            pred = _fit_simple(values, horizon)

    pred = np.clip(pred, 0, None)  # demand can't be negative

    last = values.index[-1]
    points = []
    for k, qty in enumerate(pred, start=1):
        start = last + (pd.Timedelta(days=7 * k) if unit == "week" else pd.DateOffset(months=k))
        points.append(ForecastPoint(period_start=start.date(), predicted_qty=round(float(qty), 2)))

    return ForecastResult(
        points=points, model_name=model_name, model_version=MODEL_VERSION,
        generated_at=datetime.now(timezone.utc), unit=unit, horizon=horizon,
    )
