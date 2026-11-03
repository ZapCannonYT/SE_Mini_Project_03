"""Unit tests for analytics/preprocessing.py (TC-FCST-01, TC-FCST-02)."""
from datetime import date, timedelta

import pytest

from app.analytics.preprocessing import (
    InsufficientHistoryError,
    build_series,
    validate_rows,
)


def daily_rows(start: date, days: int, qty: float = 1):
    return [
        {"sale_date": (start + timedelta(days=i)).isoformat(), "quantity_sold": qty}
        for i in range(days)
    ]


MONDAY = date(2024, 1, 1)  # 2024-01-01 is a Monday


def test_weekly_aggregation_sums_each_week():
    series = build_series(daily_rows(MONDAY, 70, qty=2), unit="week")  # 10 weeks
    assert len(series) == 10
    assert (series == 14).all()  # 7 days x 2
    assert series.index[0].date() == MONDAY


def test_monthly_aggregation_uses_first_of_month():
    rows = daily_rows(date(2024, 1, 1), 366, qty=1)  # all of 2024
    series = build_series(rows, unit="month")
    assert len(series) == 12
    assert series.index[0].date() == date(2024, 1, 1)
    assert series.iloc[0] == 31 and series.iloc[1] == 29  # Jan, Feb (leap year)


def test_missing_periods_are_filled_with_zero():
    rows = daily_rows(MONDAY, 7, qty=5) + daily_rows(MONDAY + timedelta(weeks=9), 7, qty=5)
    series = build_series(rows, unit="week")
    assert len(series) == 10
    assert series.iloc[0] == 35 and series.iloc[9] == 35
    assert (series.iloc[1:9] == 0).all()


def test_duplicate_dates_are_dropped_last_wins():
    rows = daily_rows(MONDAY, 70, qty=1)
    rows.append({"sale_date": MONDAY.isoformat(), "quantity_sold": 10})  # duplicate date
    series = build_series(rows, unit="week")
    assert series.iloc[0] == 10 + 6  # first day replaced by 10, other 6 days = 1 each


def test_fewer_than_8_periods_raises_insufficient_history():  # TC-FCST-02
    with pytest.raises(InsufficientHistoryError):
        build_series(daily_rows(MONDAY, 35), unit="week")  # 5 weeks


def test_exactly_8_periods_is_accepted():
    assert len(build_series(daily_rows(MONDAY, 56), unit="week")) == 8


def test_empty_history_raises_insufficient_history():
    with pytest.raises(InsufficientHistoryError):
        build_series([], unit="week")


@pytest.mark.parametrize(
    "bad_row",
    [
        {"sale_date": "2024-01-01", "quantity_sold": -3},       # negative
        {"sale_date": "2024-01-01", "quantity_sold": "abc"},    # not a number
        {"sale_date": "01/01/2024", "quantity_sold": 5},        # wrong date format
        {"sale_date": "2024-01-01"},                            # missing quantity
        {"quantity_sold": 5},                                   # missing date
    ],
)
def test_invalid_rows_are_rejected(bad_row):
    with pytest.raises(ValueError):
        validate_rows([bad_row])


def test_unknown_unit_is_rejected():
    with pytest.raises(ValueError):
        build_series(daily_rows(MONDAY, 70), unit="day")
