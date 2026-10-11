from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._common import utcnow

if TYPE_CHECKING:
    from app.models.product import Product


class Inventory(Base):
    """Current stock for one product (one row per product)."""

    __tablename__ = "inventory"
    __table_args__ = (CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    product: Mapped["Product"] = relationship(back_populates="inventory")
