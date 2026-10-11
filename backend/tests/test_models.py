from datetime import date

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.models import (
    AuditLog,
    Forecast,
    ForecastPoint,
    HorizonUnit,
    Inventory,
    Product,
    Recommendation,
    RiskLevel,
    Role,
    SalesRecord,
    Setting,
    User,
)


def make_product(db, sku="SKU-001", **kwargs):
    product = Product(sku=sku, name=kwargs.pop("name", "Test product"), **kwargs)
    db.add(product)
    db.commit()
    return product


def test_all_tables_are_created(engine):
    tables = set(inspect(engine).get_table_names())
    assert tables == {
        "users",
        "products",
        "inventory",
        "sales_records",
        "forecasts",
        "forecast_points",
        "recommendations",
        "audit_logs",
        "settings",
    }


def test_user_defaults_and_role(db):
    db.add(User(name="Admin", email="admin@dfip.test", password_hash="hashed", role=Role.ADMIN))
    db.commit()

    user = db.scalar(select(User).where(User.email == "admin@dfip.test"))
    assert user.role is Role.ADMIN
    assert user.is_active is True
    assert user.created_at is not None


def test_user_email_must_be_unique(db):
    db.add(User(name="A", email="same@dfip.test", password_hash="x"))
    db.commit()
    db.add(User(name="B", email="same@dfip.test", password_hash="y"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_product_defaults_and_unique_sku(db):
    product = make_product(db)
    assert product.safety_stock == 0
    assert product.overstock_factor == 1.5
    assert product.is_active is True

    db.add(Product(sku="SKU-001", name="Duplicate"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_inventory_belongs_to_product(db):
    product = make_product(db)
    db.add(Inventory(product_id=product.id, quantity=120))
    db.commit()

    db.expire_all()
    assert db.get(Product, product.id).inventory.quantity == 120


def test_inventory_rejects_negative_quantity(db):
    product = make_product(db)
    db.add(Inventory(product_id=product.id, quantity=-5))
    with pytest.raises(IntegrityError):
        db.commit()


def test_inventory_requires_existing_product(db):
    db.add(Inventory(product_id=999, quantity=1))
    with pytest.raises(IntegrityError):
        db.commit()


def test_sales_one_record_per_product_per_date(db):
    product = make_product(db)
    db.add(SalesRecord(product_id=product.id, sale_date=date(2026, 10, 1), quantity_sold=10))
    db.commit()
    db.add(SalesRecord(product_id=product.id, sale_date=date(2026, 10, 1), quantity_sold=4))
    with pytest.raises(IntegrityError):
        db.commit()


def test_sales_rejects_negative_quantity(db):
    product = make_product(db)
    db.add(SalesRecord(product_id=product.id, sale_date=date(2026, 10, 1), quantity_sold=-1))
    with pytest.raises(IntegrityError):
        db.commit()


def test_forecast_stores_metadata_and_ordered_points(db):
    product = make_product(db)
    forecast = Forecast(
        product_id=product.id,
        horizon=2,
        unit=HorizonUnit.WEEK,
        model_name="holt_winters",
        model_version="1.0",
        points=[
            ForecastPoint(period_start=date(2026, 10, 19), predicted_qty=12.5),
            ForecastPoint(period_start=date(2026, 10, 12), predicted_qty=10.0),
        ],
    )
    db.add(forecast)
    db.commit()

    db.expire_all()
    stored = db.get(Forecast, forecast.id)
    assert stored.unit is HorizonUnit.WEEK
    assert stored.model_name == "holt_winters"
    assert stored.generated_at is not None
    assert [p.period_start for p in stored.points] == [date(2026, 10, 12), date(2026, 10, 19)]


def test_deleting_forecast_removes_its_points(db):
    product = make_product(db)
    forecast = Forecast(
        product_id=product.id,
        horizon=1,
        unit=HorizonUnit.MONTH,
        model_name="ses",
        model_version="1.0",
        points=[ForecastPoint(period_start=date(2026, 11, 1), predicted_qty=30)],
    )
    db.add(forecast)
    db.commit()

    db.delete(forecast)
    db.commit()
    assert db.scalars(select(ForecastPoint)).all() == []


def test_recommendation_keeps_planning_inputs(db):
    product = make_product(db, safety_stock=20)
    forecast = Forecast(product_id=product.id, horizon=4, unit=HorizonUnit.WEEK, model_name="ses", model_version="1.0")
    db.add(forecast)
    db.commit()

    db.add(
        Recommendation(
            product_id=product.id,
            forecast_id=forecast.id,
            current_stock=50,
            forecast_demand=100.0,
            safety_stock=20,
            overstock_factor=1.5,
            reorder_qty=70,
            risk=RiskLevel.STOCKOUT,
        )
    )
    db.commit()

    rec = db.scalar(select(Recommendation))
    assert (rec.current_stock, rec.forecast_demand, rec.safety_stock, rec.reorder_qty) == (50, 100.0, 20, 70)
    assert rec.risk is RiskLevel.STOCKOUT


def test_audit_log_and_settings(db):
    user = User(name="Admin", email="admin@dfip.test", password_hash="x", role=Role.ADMIN)
    db.add(user)
    db.commit()

    db.add(AuditLog(actor_id=user.id, action="login", result="success"))
    db.add(Setting(key="default_overstock_factor", value="1.5"))
    db.commit()

    log = db.scalar(select(AuditLog))
    assert (log.actor_id, log.action, log.result) == (user.id, "login", "success")
    assert log.timestamp is not None
    assert db.get(Setting, "default_overstock_factor").value == "1.5"
