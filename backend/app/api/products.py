from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.db import get_db
from app.models import Product, Role, User
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services import product_service

router = APIRouter(prefix="/api/products", tags=["Products"])

any_user = require_role(Role.ADMIN.value, Role.PLANNER.value, Role.VIEWER.value)
admin_only = require_role(Role.ADMIN.value)


def to_out(product: Product) -> ProductOut:
    return ProductOut(
        id=product.id,
        sku=product.sku,
        name=product.name,
        category=product.category,
        unit=product.unit,
        safety_stock=product.safety_stock,
        overstock_factor=product.overstock_factor,
        is_active=product.is_active,
        created_at=product.created_at,
        quantity=product.inventory.quantity if product.inventory else 0,
    )


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    """Create a product/SKU with its starting stock (DFIP-F-004). Admin only."""
    return to_out(product_service.create_product(db, data, user))


@router.get("", response_model=list[ProductOut])
def list_products(
    include_inactive: bool = Query(False, description="Also return deactivated products."),
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
):
    return [to_out(p) for p in product_service.list_products(db, include_inactive)]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db), _user: User = Depends(any_user)):
    return to_out(product_service.get_product(db, product_id))


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int, data: ProductUpdate, db: Session = Depends(get_db), _user: User = Depends(admin_only)
):
    """Update product details; only the fields sent are changed. Admin only."""
    return to_out(product_service.update_product(db, product_id, data))


@router.patch("/{product_id}/deactivate", response_model=ProductOut)
def deactivate_product(product_id: int, db: Session = Depends(get_db), _user: User = Depends(admin_only)):
    """Hide a product from normal lists and planning without deleting its history. Admin only."""
    return to_out(product_service.deactivate_product(db, product_id))
