"""Read validated planning defaults from the shared settings table."""
import math
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.analytics.preprocessing import MIN_PERIODS
from app.core.errors import AppError
from app.models import Setting

DEFAULT_SAFETY_STOCK_KEY = "default_safety_stock"
DEFAULT_OVERSTOCK_FACTOR_KEY = "default_overstock_factor"
MINIMUM_HISTORY_PERIODS_KEY = "minimum_history_periods"


@dataclass(frozen=True)
class PlanningSettings:
    default_safety_stock: int | None
    default_overstock_factor: float | None
    minimum_history_periods: int


def _read_integer(db: Session, key: str, *, default: int | None, minimum: int) -> int | None:
    row = db.get(Setting, key)
    if row is None:
        return default
    try:
        value = int(row.value)
    except (TypeError, ValueError):
        raise AppError(500, "invalid_stored_setting", f"Setting '{key}' must be a whole number.") from None
    if value < minimum:
        raise AppError(500, "invalid_stored_setting", f"Setting '{key}' must be at least {minimum}.")
    return value


def _read_factor(db: Session) -> float | None:
    row = db.get(Setting, DEFAULT_OVERSTOCK_FACTOR_KEY)
    if row is None:
        return None
    try:
        value = float(row.value)
    except (TypeError, ValueError):
        raise AppError(
            500, "invalid_stored_setting", "Setting 'default_overstock_factor' must be a number."
        ) from None
    if not math.isfinite(value) or not 1 <= value <= 10:
        raise AppError(
            500, "invalid_stored_setting", "Setting 'default_overstock_factor' must be between 1 and 10."
        )
    return value


def get_planning_settings(db: Session) -> PlanningSettings:
    """Return saved settings, with the forecasting threshold's code default.

    Safety stock and overstock factor remain ``None`` when no global setting
    exists so existing per-product values continue to work as their fallback.
    """
    return PlanningSettings(
        default_safety_stock=_read_integer(
            db, DEFAULT_SAFETY_STOCK_KEY, default=None, minimum=0
        ),
        default_overstock_factor=_read_factor(db),
        minimum_history_periods=_read_integer(
            db, MINIMUM_HISTORY_PERIODS_KEY, default=MIN_PERIODS, minimum=1
        ),
    )
