from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Sku = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,49}$")]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Category = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
Unit = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
OverstockFactor = Annotated[float, Field(gt=0, le=10)]


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: Sku = Field(description="Letters, digits, '-' or '_' (max 50). Cannot be changed later.")
    name: Name
    category: Category | None = None
    unit: Unit = "unit"
    safety_stock: NonNegativeInt = 0
    overstock_factor: OverstockFactor = 1.5
    initial_quantity: NonNegativeInt = Field(0, description="Starting stock for the new product.")


class ProductUpdate(BaseModel):
    """Only the fields sent are changed. The SKU cannot be changed."""

    model_config = ConfigDict(extra="forbid")

    name: Name | None = None
    category: Category | None = None
    unit: Unit | None = None
    safety_stock: NonNegativeInt | None = None
    overstock_factor: OverstockFactor | None = None


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    category: str | None
    unit: str
    safety_stock: int
    overstock_factor: float
    is_active: bool
    created_at: datetime
    quantity: int = Field(description="Current stock on hand.")
