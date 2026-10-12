from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Inventory, Product, User
from app.schemas.product import ProductCreate, ProductUpdate

# Fields that may be omitted in an update but never set to null.
_REQUIRED_ON_UPDATE = ("name", "unit", "safety_stock", "overstock_factor")


def list_products(db: Session, include_inactive: bool = False) -> list[Product]:
    stmt = select(Product).order_by(Product.sku)
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    return list(db.scalars(stmt))


def get_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise AppError(404, "product_not_found", f"Product {product_id} does not exist.")
    return product


def create_product(db: Session, data: ProductCreate, actor: User) -> Product:
    duplicate = db.scalar(select(Product.id).where(func.lower(Product.sku) == data.sku.lower()))
    if duplicate is not None:
        raise AppError(409, "sku_exists", f"A product with SKU '{data.sku}' already exists.")

    product = Product(**data.model_dump(exclude={"initial_quantity"}))
    product.inventory = Inventory(quantity=data.initial_quantity, updated_by=actor.id)
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "sku_exists", f"A product with SKU '{data.sku}' already exists.") from None
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    changes = data.model_dump(exclude_unset=True)

    empty = [field for field in _REQUIRED_ON_UPDATE if field in changes and changes[field] is None]
    if empty:
        raise AppError(
            422,
            "validation_error",
            "Some fields are missing or invalid.",
            [{"field": field, "message": "Cannot be empty"} for field in empty],
        )

    for field, value in changes.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def deactivate_product(db: Session, product_id: int) -> Product:
    product = get_product(db, product_id)
    if product.is_active:
        product.is_active = False
        db.commit()
        db.refresh(product)
    return product
