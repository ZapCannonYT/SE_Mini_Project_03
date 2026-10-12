from datetime import date

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.db import get_db
from app.models import Role, SalesRecord, User
from app.schemas.sales import ImportResult, SalesCreate, SalesOut
from app.services import sales_service

router = APIRouter(prefix="/api/sales", tags=["Sales"])

any_user = require_role(Role.ADMIN.value, Role.PLANNER.value, Role.VIEWER.value)
can_add_sales = require_role(Role.ADMIN.value, Role.PLANNER.value)


def to_out(record: SalesRecord) -> SalesOut:
    return SalesOut(
        id=record.id,
        product_id=record.product_id,
        sku=record.product.sku,
        sale_date=record.sale_date,
        quantity_sold=record.quantity_sold,
        created_by=record.created_by,
        created_at=record.created_at,
    )


@router.post("", response_model=SalesOut, status_code=status.HTTP_201_CREATED)
def add_sale(data: SalesCreate, db: Session = Depends(get_db), user: User = Depends(can_add_sales)):
    """Record units sold for one product on one date (DFIP-F-007). Admin or planner."""
    return to_out(sales_service.add_sale(db, data, user))


@router.get("", response_model=list[SalesOut])
def list_sales(
    product_id: int | None = Query(None, description="Only this product."),
    date_from: date | None = Query(None, alias="from", description="On or after this date (YYYY-MM-DD)."),
    date_to: date | None = Query(None, alias="to", description="On or before this date (YYYY-MM-DD)."),
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
):
    """Historical sales filtered by product and date range (DFIP-F-009)."""
    return [to_out(r) for r in sales_service.list_sales(db, product_id, date_from, date_to)]


@router.post("/import", response_model=ImportResult)
def import_sales(
    file: UploadFile = File(..., description="CSV with header: sku,date,quantity_sold"),
    db: Session = Depends(get_db),
    user: User = Depends(can_add_sales),
):
    """Import historical sales from CSV (DFIP-F-008). Valid rows are saved; invalid rows are listed by line number."""
    content = file.file.read(sales_service.MAX_IMPORT_BYTES + 1)
    return sales_service.import_sales(db, content, user)
