
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
OverstockFactor = Annotated[float, Field(ge=1, le=10)]
PositiveInt = Annotated[int, Field(strict=True, ge=1)]


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_safety_stock: NonNegativeInt | None = None
    default_overstock_factor: OverstockFactor | None = None
    minimum_history_periods: PositiveInt | None = None


class SettingsOut(BaseModel):
    default_safety_stock: int | None = None
    default_overstock_factor: float | None = None
    minimum_history_periods: int = 8
