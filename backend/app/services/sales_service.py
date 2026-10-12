import csv
import io
import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.models import Product, SalesRecord, User
from app.schemas.sales import ImportResult, ImportRowError, SalesCreate
from app.services.product_service import get_product

MAX_IMPORT_BYTES = 2 * 1024 * 1024  # 2 MB is far more than a few years of daily sales for a mini-project
REQUIRED_COLUMNS = ("sku", "date", "quantity_sold")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_WHOLE_NUMBER_RE = re.compile(r"^\d+$")


def add_sale(db: Session, data: SalesCreate, actor: User) -> SalesRecord:
    product = get_product(db, data.product_id)
    if not product.is_active:
        raise AppError(409, "product_inactive", f"Product {product.sku} is deactivated; sales cannot be added.")

    duplicate = db.scalar(
        select(SalesRecord.id).where(
            SalesRecord.product_id == product.id, SalesRecord.sale_date == data.sale_date
        )
    )
    if duplicate is not None:
        raise AppError(409, "sale_exists", f"Sales for {product.sku} on {data.sale_date} are already recorded.")

    record = SalesRecord(
        product_id=product.id, sale_date=data.sale_date, quantity_sold=data.quantity_sold, created_by=actor.id
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "sale_exists", f"Sales for {product.sku} on {data.sale_date} are already recorded.") from None
    db.refresh(record)
    return record


def list_sales(
    db: Session, product_id: int | None = None, date_from: date | None = None, date_to: date | None = None
) -> list[SalesRecord]:
    if date_from and date_to and date_from > date_to:
        raise AppError(400, "invalid_date_range", "'from' must be on or before 'to'.")

    stmt = (
        select(SalesRecord)
        .options(joinedload(SalesRecord.product))
        .order_by(SalesRecord.sale_date, SalesRecord.product_id)
    )
    if product_id is not None:
        stmt = stmt.where(SalesRecord.product_id == product_id)
    if date_from is not None:
        stmt = stmt.where(SalesRecord.sale_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(SalesRecord.sale_date <= date_to)
    return list(db.scalars(stmt))


def get_sales_history(db: Session, product_id: int) -> list[dict]:
    """Sales rows for one product, oldest first, in the shape `analytics.preprocessing.build_series` expects."""
    rows = db.execute(
        select(SalesRecord.sale_date, SalesRecord.quantity_sold)
        .where(SalesRecord.product_id == product_id)
        .order_by(SalesRecord.sale_date)
    )
    return [{"sale_date": sale_date, "quantity_sold": qty} for sale_date, qty in rows]


def parse_csv(content: bytes) -> list[tuple[int, dict[str, str]]]:
    """Return (line number, {sku, date, quantity_sold}) for every non-blank data row."""
    if len(content) > MAX_IMPORT_BYTES:
        raise AppError(413, "file_too_large", f"The file is larger than {MAX_IMPORT_BYTES // (1024 * 1024)} MB.")
    try:
        text = content.decode("utf-8-sig")  # utf-8-sig also strips the BOM Excel adds
    except UnicodeDecodeError:
        raise AppError(400, "invalid_csv_format", "The file must be a UTF-8 encoded CSV.") from None

    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader, None)
        if header is None:
            raise AppError(400, "invalid_csv_format", "The file is empty.")
        columns = [name.strip().lower() for name in header]
        missing = [name for name in REQUIRED_COLUMNS if name not in columns]
        if missing:
            raise AppError(
                400,
                "invalid_csv_format",
                f"Missing column(s): {', '.join(missing)}. Expected header: {','.join(REQUIRED_COLUMNS)}",
            )

        rows = []
        for values in reader:
            if not any(value.strip() for value in values):
                continue
            row = {name: (values[i].strip() if i < len(values) else "") for i, name in enumerate(columns)}
            rows.append((reader.line_num, row))
    except csv.Error as err:
        raise AppError(400, "invalid_csv_format", f"The file is not a valid CSV: {err}") from None

    if not rows:
        raise AppError(400, "invalid_csv_format", "The file has no data rows.")
    return rows


def import_sales(db: Session, content: bytes, actor: User) -> ImportResult:
    """Import valid rows in one transaction and report every invalid row (DFIP-F-008)."""
    rows = parse_csv(content)
    products = {p.sku.lower(): p for p in db.scalars(select(Product))}
    existing = set(db.execute(select(SalesRecord.product_id, SalesRecord.sale_date)).tuples())

    errors: list[ImportRowError] = []
    new_records: list[SalesRecord] = []
    seen_in_file: set[tuple[int, date]] = set()
    today = date.today()

    for line, row in rows:
        problems: list[str] = []

        sku = row["sku"]
        product = products.get(sku.lower())
        if not sku:
            problems.append("SKU is empty")
        elif product is None:
            problems.append(f"Unknown SKU '{sku}'")
        elif not product.is_active:
            problems.append(f"Product '{sku}' is deactivated")

        sale_date = None
        raw_date = row["date"]
        if not _DATE_RE.match(raw_date):
            problems.append(f"Invalid date '{raw_date}' (use YYYY-MM-DD)")
        else:
            try:
                sale_date = date.fromisoformat(raw_date)
            except ValueError:
                problems.append(f"Invalid date '{raw_date}' (use YYYY-MM-DD)")
            else:
                if sale_date > today:
                    problems.append(f"Date {raw_date} is in the future")
                    sale_date = None

        raw_qty = row["quantity_sold"]
        if not _WHOLE_NUMBER_RE.match(raw_qty):
            problems.append(f"Invalid quantity '{raw_qty}' (must be a whole number >= 0)")

        if not problems and product is not None and sale_date is not None:
            key = (product.id, sale_date)
            if key in seen_in_file:
                problems.append(f"Duplicate of an earlier row for {product.sku} on {raw_date}")
            elif key in existing:
                problems.append(f"Sales for {product.sku} on {raw_date} are already recorded")
            else:
                seen_in_file.add(key)

        if problems:
            errors.append(ImportRowError(row=line, error="; ".join(problems)))
        else:
            new_records.append(
                SalesRecord(
                    product_id=product.id, sale_date=sale_date, quantity_sold=int(raw_qty), created_by=actor.id
                )
            )

    if new_records:
        db.add_all(new_records)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise AppError(409, "import_conflict", "Some rows clashed with sales saved at the same time; nothing was imported.") from None

    return ImportResult(total_rows=len(rows), imported=len(new_records), rejected=len(errors), errors=errors)
