import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._common import utcnow


class RiskLevel(str, enum.Enum):
    NONE = "none"
    STOCKOUT = "stockout"
    OVERSTOCK = "overstock"


class Recommendation(Base):
    """Reorder recommendation and risk, storing every input used (DFIP-F-013 to F-016)."""

    __tablename__ = "recommendations"
    __table_args__ = (CheckConstraint("reorder_qty >= 0", name="ck_recommendations_reorder_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    forecast_id: Mapped[int] = mapped_column(ForeignKey("forecasts.id", ondelete="CASCADE"), index=True)
    current_stock: Mapped[int] = mapped_column(Integer)
    forecast_demand: Mapped[float] = mapped_column(Float)
    safety_stock: Mapped[int] = mapped_column(Integer)
    overstock_factor: Mapped[float] = mapped_column(Float)
    reorder_qty: Mapped[int] = mapped_column(Integer)
    risk: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, native_enum=False, length=10, values_callable=lambda e: [m.value for m in e]),
        default=RiskLevel.NONE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
