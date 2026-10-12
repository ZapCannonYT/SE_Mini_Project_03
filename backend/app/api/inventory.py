from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.db import get_db
from app.models import Product, Role, User
from app.schemas.inventory import InventoryOut, InventoryUpdate
from app.services import inventory_service

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

any_user = require_role(Role.ADMIN.value, Role.PLANNER.value, Role.VIEWER.value)
can_update_stock = require_role(Role.ADMIN.value, Role.PLANNER.value)


def to_out(product: Product) -> InventoryOut:
    inventory = product.inventory
    return InventoryOut(
        product_id=product.id,
        sku=product.sku,
        name=product.name,
        quantity=inventory.quantity if inventory else 0,
        updated_at=inventory.updated_at if inventory else None,
        updated_by=inventory.updated_by if inventory else None,
    )


@router.get("", response_model=list[InventoryOut])
def list_stock(db: Session = Depends(get_db), _user: User = Depends(any_user)):
    """Current stock for every active product (DFIP-F-005)."""
    return [to_out(p) for p in inventory_service.list_stock(db)]


@router.get("/{product_id}", response_model=InventoryOut)
def get_stock(product_id: int, db: Session = Depends(get_db), _user: User = Depends(any_user)):
    return to_out(inventory_service.get_stock(db, product_id))


@router.put("/{product_id}", response_model=InventoryOut)
def set_stock(
    product_id: int,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(can_update_stock),
):
    """Set the current stock quantity (DFIP-F-006). Admin or planner."""
    return to_out(inventory_service.set_quantity(db, product_id, data.quantity, user))
