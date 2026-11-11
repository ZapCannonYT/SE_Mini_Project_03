import csv
import io
import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.models import Product, SalesRecord, User
from app.schemas.sales import ImportRejection, ImportResult, SalesCreate
from app.services.product_service import get_product

MAX_IMPORT_BYTES = 2 * 1024 * 1024  # 2 MB is far more than a few years of daily sales for a mini-project
CSV_HEADER = ("sku", "date", "quantity_sold")

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INTEGER = re.compile(r"^-?\d+$")


def _sale_exists(product: Product, sale_date: date) -> AppError:
    return AppError(409, "sale_exists", f"Sales for {product.sku} on {sale_date} are already recorded.")


def add_sale(db: Session, data: SalesCreate, actor: User) -> SalesRecord:
    product = get_product(db, data.product_id)
    if not product.is_active:
        raise AppError(409, "product_inactive", f"Product {product.sku} is deactivated; sales cannot be added.")

    duplicate = db.scalar(
        select(SalesRecord.id).where(SalesRecord.product_id == product.id, SalesRecord.sale_date == data.sale_date)
    )
    if duplicate is not None:
        raise _sale_exists(product, data.sale_date)

    record = SalesRecord(
        product_id=product.id, sale_date=data.sale_date, quantity_sold=data.quantity_sold, created_by=actor.id
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _sale_exists(product, data.sale_date) from None
    db.refresh(record)
    return record


def list_sales(
    db: Session, product_id: int | None = None, start_date: date | None = None, end_date: date | None = None
) -> list[SalesRecord]:
    """Sales matching the filters, newest date first (DFIP-F-009)."""
    if start_date and end_date and start_date > end_date:
        raise AppError(
            422,
            "validation_error",
            "Some fields are missing or invalid.",
            [{"field": "start_date", "message": "Start date must be on or before end date"}],
        )

    stmt = (
        select(SalesRecord)
        .options(joinedload(SalesRecord.product))
        .order_by(SalesRecord.sale_date.desc(), SalesRecord.id.desc())
    )
    if product_id is not None:
        stmt = stmt.where(SalesRecord.product_id == product_id)
    if start_date is not None:
        stmt = stmt.where(SalesRecord.sale_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(SalesRecord.sale_date <= end_date)
    return list(db.scalars(stmt))


def get_sales_history(db: Session, product_id: int) -> list[dict]:
    """Sales rows for one product, oldest first, in the shape `analytics.preprocessing` expects."""
    rows = db.execute(
        select(SalesRecord.sale_date, SalesRecord.quantity_sold)
        .where(SalesRecord.product_id == product_id)
        .order_by(SalesRecord.sale_date)
    )
    return [{"sale_date": sale_date, "quantity_sold": qty} for sale_date, qty in rows]


def _invalid_csv(message: str) -> AppError:
    return AppError(422, "invalid_csv", message, [])


def parse_csv(content: bytes) -> list[tuple[int, list[str]]]:
    """Return (line number, cells) for every non-blank data row; reject the whole file if it cannot be read."""
    if len(content) > MAX_IMPORT_BYTES:
        raise AppError(413, "file_too_large", f"The file is larger than {MAX_IMPORT_BYTES // (1024 * 1024)} MB.", [])
    try:
        text = content.decode("utf-8-sig")  # utf-8-sig also strips the BOM Excel adds
    except UnicodeDecodeError:
        raise _invalid_csv("The file must be a UTF-8 encoded CSV.") from None
    if not text.strip():
        raise _invalid_csv("The CSV file is empty")

    reader = csv.reader(io.StringIO(text))
    try:
        header = [name.strip().lower() for name in next(reader)]
        if tuple(header) != CSV_HEADER:
            raise _invalid_csv(f"Header must be exactly: {','.join(CSV_HEADER)}")
        rows = [(reader.line_num, [v.strip() for v in values]) for values in reader if any(v.strip() for v in values)]
    except csv.Error as err:
        raise _invalid_csv(f"The file is not a valid CSV: {err}") from None
    return rows


def _check_row(cells, products, today) -> tuple[str | None, Product | None, date | None, int | None]:
    """First problem with one CSV row, or None plus the parsed values."""
    if len(cells) != len(CSV_HEADER):
        return "Expected 3 columns: sku,date,quantity_sold", None, None, None
    sku, raw_date, raw_qty = cells

    product = products.get(sku.lower())
    if not sku:
        return "SKU is empty", None, None, None
    if product is None:
        return f"Unknown SKU: {sku}", None, None, None
    if not product.is_active:
        return f"Product {product.sku} is deactivated", None, None, None

    try:
        if not _ISO_DATE.match(raw_date):
            raise ValueError
        sale_date = date.fromisoformat(raw_date)
    except ValueError:
        return "Date must be in YYYY-MM-DD format", None, None, None
    if sale_date > today:
        return "Date cannot be in the future", None, None, None

    if not _INTEGER.match(raw_qty):
        return "Quantity sold must be a whole number", None, None, None
    quantity = int(raw_qty)
    if quantity < 0:
        return "Quantity sold cannot be negative", None, None, None

    return None, product, sale_date, quantity


def import_sales(db: Session, content: bytes, actor: User) -> ImportResult:
    """Save every valid row in one transaction and report each invalid row with its line number (DFIP-F-008)."""
    rows = parse_csv(content)
    products = {p.sku.lower(): p for p in db.scalars(select(Product))}
    stored = set(db.execute(select(SalesRecord.product_id, SalesRecord.sale_date)).tuples())
    today = date.today()

    rejected: list[ImportRejection] = []
    new_records: list[SalesRecord] = []
    seen_in_file: set[tuple[int, date]] = set()

    for line, cells in rows:
        problem, product, sale_date, quantity = _check_row(cells, products, today)
        if problem is None:
            key = (product.id, sale_date)
            if key in seen_in_file:
                problem = "Duplicate product and date in this file"
            elif key in stored:
                problem = "A sales record already exists for this product and date"

        if problem:
            rejected.append(ImportRejection(row=line, message=problem))
            continue
        seen_in_file.add(key)
        new_records.append(
            SalesRecord(product_id=product.id, sale_date=sale_date, quantity_sold=quantity, created_by=actor.id)
        )

    if new_records:
        db.add_all(new_records)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise AppError(
                409, "import_conflict", "Some rows clashed with sales saved at the same time; nothing was imported.", []
            ) from None

    return ImportResult(imported=len(new_records), rejected=rejected)
