from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ForecastCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(strict=True, gt=0)
    horizon: int = Field(strict=True)
    unit: Literal["week", "month"]


class ForecastPointOut(BaseModel):
    period_start: date
    predicted_qty: float


class ForecastOut(BaseModel):
    id: int
    product_id: int
    horizon: int
    unit: str
    model_name: str
    model_version: str
    generated_at: datetime
    points: list[ForecastPointOut]
