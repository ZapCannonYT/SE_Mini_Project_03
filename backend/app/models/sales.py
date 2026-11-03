from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._common import utcnow

if TYPE_CHECKING:
    from app.models.product import Product


class SalesRecord(Base):
    """Quantity of one product sold on one date (the history used for forecasting)."""

    __tablename__ = "sales_records"
    __table_args__ = (
        UniqueConstraint("product_id", "sale_date", name="uq_sales_product_date"),
        CheckConstraint("quantity_sold >= 0", name="ck_sales_quantity_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    sale_date: Mapped[date] = mapped_column(Date, index=True)
    quantity_sold: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    product: Mapped["Product"] = relationship(back_populates="sales")
