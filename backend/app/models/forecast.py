import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._common import utcnow

if TYPE_CHECKING:
    from app.models.product import Product


class HorizonUnit(str, enum.Enum):
    WEEK = "week"
    MONTH = "month"


class Forecast(Base):
    """One forecast run for a product, with the model metadata required by DFIP-F-012."""

    __tablename__ = "forecasts"
    __table_args__ = (CheckConstraint("horizon > 0", name="ck_forecasts_horizon_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    horizon: Mapped[int] = mapped_column(Integer)
    unit: Mapped[HorizonUnit] = mapped_column(
        Enum(HorizonUnit, native_enum=False, length=10, values_callable=lambda e: [m.value for m in e])
    )
    model_name: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[str] = mapped_column(String(50))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    product: Mapped["Product"] = relationship(back_populates="forecasts")
    points: Mapped[list["ForecastPoint"]] = relationship(
        back_populates="forecast", cascade="all, delete-orphan", order_by="ForecastPoint.period_start"
    )


class ForecastPoint(Base):
    """Predicted demand for one period of a forecast."""

    __tablename__ = "forecast_points"
    __table_args__ = (CheckConstraint("predicted_qty >= 0", name="ck_forecast_points_qty_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    forecast_id: Mapped[int] = mapped_column(ForeignKey("forecasts.id", ondelete="CASCADE"), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    predicted_qty: Mapped[float] = mapped_column(Float)

    forecast: Mapped[Forecast] = relationship(back_populates="points")
