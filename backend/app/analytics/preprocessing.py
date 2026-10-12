"""Preprocessing: raw sales rows -> clean weekly/monthly demand series.

Pure Python + pandas. No database or API needed (SRS DFIP-F-010, SAD analytics layer).
"""
from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any, Iterable, Mapping

import pandas as pd

MIN_PERIODS = 8
VALID_UNITS = ("week", "month")


class InsufficientHistoryError(ValueError):
    """Raised when there are too few periods of sales history to forecast."""


def _to_date(value: Any) -> date:
    if isinstance(value, datetime):  # datetime is a subclass of date, so check first
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            pass
    raise ValueError(f"Invalid date: {value!r} (expected YYYY-MM-DD)")


def _to_quantity(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError(f"Invalid quantity: {value!r}")
    try:
        qty = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid quantity: {value!r}") from None
    if not math.isfinite(qty) or qty < 0:
        raise ValueError(f"Invalid quantity: {value!r} (must be a number >= 0)")
    return qty


def validate_rows(rows: Iterable[Mapping[str, Any]]) -> list[tuple[date, float]]:
    """Check every row has a valid `sale_date` and `quantity_sold`.

    Returns a list of (date, quantity). Raises ValueError naming the bad row.
    """
    clean: list[tuple[date, float]] = []
    for i, row in enumerate(rows):
        try:
            clean.append((_to_date(row["sale_date"]), _to_quantity(row["quantity_sold"])))
        except KeyError as missing:
            raise ValueError(f"Row {i}: missing field {missing}") from None
        except ValueError as err:
            raise ValueError(f"Row {i}: {err}") from None
    return clean


def build_series(
    rows: Iterable[Mapping[str, Any]],
    unit: str = "week",
    min_periods: int = MIN_PERIODS,
) -> pd.Series:
    """Aggregate sales rows into a weekly or monthly demand series.

    - weeks start on Monday, months start on the 1st (index = period start)
    - periods with no sales are filled with 0
    - duplicate dates are dropped (the last row for a date wins)
    - raises InsufficientHistoryError if fewer than `min_periods` periods
    """
    if unit not in VALID_UNITS:
        raise ValueError(f"unit must be one of {VALID_UNITS}, got {unit!r}")

    by_date: dict[date, float] = {}
    for sale_date, qty in validate_rows(rows):
        by_date[sale_date] = qty  # duplicate date -> last one wins
    if not by_date:
        raise InsufficientHistoryError("No sales history provided.")

    daily = pd.Series(by_date, dtype=float)
    daily.index = pd.to_datetime(daily.index)

    if unit == "week":
        starts = daily.index - pd.to_timedelta(daily.index.weekday, unit="D")
        freq = "7D"
    else:
        starts = daily.index.to_period("M").to_timestamp()
        freq = "MS"

    grouped = daily.groupby(starts).sum()
    full_index = pd.date_range(grouped.index.min(), grouped.index.max(), freq=freq)
    series = grouped.reindex(full_index, fill_value=0.0)
    series.index.name = "period_start"
    series.name = "quantity"

    if len(series) < min_periods:
        raise InsufficientHistoryError(
            f"Need at least {min_periods} {unit}s of history, got {len(series)}."
        )
    return series
