from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._common import utcnow

if TYPE_CHECKING:
    from app.models.forecast import Forecast
    from app.models.inventory import Inventory
    from app.models.sales import SalesRecord


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("safety_stock >= 0", name="ck_products_safety_stock_non_negative"),
        CheckConstraint("overstock_factor > 0", name="ck_products_overstock_factor_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(20), default="unit")
    safety_stock: Mapped[int] = mapped_column(Integer, default=0)
    overstock_factor: Mapped[float] = mapped_column(Float, default=1.5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    inventory: Mapped["Inventory | None"] = relationship(
        back_populates="product", uselist=False, cascade="all, delete-orphan"
    )
    sales: Mapped[list["SalesRecord"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    forecasts: Mapped[list["Forecast"]] = relationship(back_populates="product", cascade="all, delete-orphan")
