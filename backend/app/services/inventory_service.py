from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Inventory, Product, User
from app.models._common import utcnow
from app.services.product_service import get_product, list_products


def list_stock(db: Session) -> list[Product]:
    """Active products with their inventory rows loaded."""
    return list_products(db)


def get_stock(db: Session, product_id: int) -> Product:
    return get_product(db, product_id)


def set_quantity(db: Session, product_id: int, quantity: int, actor: User) -> Product:
    product = get_product(db, product_id)
    if not product.is_active:
        raise AppError(409, "product_inactive", f"Product {product.sku} is deactivated; its stock cannot be changed.")

    if product.inventory is None:
        product.inventory = Inventory(product_id=product.id)
    product.inventory.quantity = quantity
    product.inventory.updated_by = actor.id
    product.inventory.updated_at = utcnow()
    db.commit()
    db.refresh(product)
    return product
