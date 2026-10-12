import re
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class SalesCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: Annotated[int, Field(strict=True, gt=0)]
    sale_date: Annotated[date, Field(description="YYYY-MM-DD, not in the future.")]
    quantity_sold: Annotated[int, Field(strict=True, ge=0, description="Whole number of units sold (>= 0).")]

    @field_validator("sale_date", mode="before")
    @classmethod
    def iso_date_string(cls, value):
        # Without this, numbers (read as Unix timestamps) and other date formats would be accepted.
        if not isinstance(value, str) or not _ISO_DATE.match(value):
            raise ValueError("Use the format YYYY-MM-DD")
        return value

    @field_validator("sale_date")
    @classmethod
    def not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Sale date cannot be in the future")
        return value


class SalesOut(BaseModel):
    id: int
    product_id: int
    sku: str
    sale_date: date
    quantity_sold: int
    created_by: int | None
    created_at: datetime


class ImportRowError(BaseModel):
    row: int = Field(description="Line number in the CSV file (the header is line 1).")
    error: str


class ImportResult(BaseModel):
    total_rows: int
    imported: int
    rejected: int
    errors: list[ImportRowError]
