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
            raise ValueError("Date must be a valid YYYY-MM-DD date")
        return value

    @field_validator("sale_date")
    @classmethod
    def not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Date cannot be in the future")
        return value


class SalesOut(BaseModel):
    id: int
    product_id: int
    sku: str
    name: str
    sale_date: date
    quantity_sold: int
    created_by: int | None = Field(description="User id of whoever recorded or imported the row.")
    created_at: datetime


class ImportRejection(BaseModel):
    row: int = Field(description="Line number in the CSV file (the header is line 1).")
    message: str


class ImportResult(BaseModel):
    imported: int
    rejected: list[ImportRejection]
