from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class InventoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Annotated[int, Field(strict=True, ge=0, description="Whole number of units on hand (>= 0).")]


class InventoryOut(BaseModel):
    product_id: int
    sku: str
    name: str
    quantity: int
    updated_at: datetime | None
    updated_by: int | None
