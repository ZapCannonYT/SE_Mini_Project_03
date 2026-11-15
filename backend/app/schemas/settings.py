
from pydantic import BaseModel, ConfigDict, Field


class SettingsUpdate(BaseModel):
    default_safety_stock: int | None = Field(default=None, ge=0)
    default_overstock_factor: float | None = Field(default=None, ge=1, le=10)
    minimum_history_periods: int | None = Field(default=None, ge=1)


class SettingsOut(BaseModel):
    default_safety_stock: int | None = None
    default_overstock_factor: float | None = None
    minimum_history_periods: int = 8

    model_config = ConfigDict(from_attributes=True)
