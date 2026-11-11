# Sample data

## Sales CSV format (`POST /api/sales/import`)

```
sku,date,quantity_sold
SKU-100,2026-09-01,12
```

| Column | Rule |
|---|---|
| `sku` | Must match an existing, active product (case-insensitive) |
| `date` | `YYYY-MM-DD`, not in the future |
| `quantity_sold` | Whole number >= 0 |

- The header must be exactly `sku,date,quantity_sold` (case-insensitive). A wrong header or an empty file returns 422 `invalid_csv` and nothing is stored.
- UTF-8 (Excel's "CSV UTF-8" is fine), max 2 MB.
- One row per product per date. Rows that repeat an earlier row in the file, or a date already stored, are rejected.
- Valid rows are saved together in one transaction; every invalid row is reported as `{row, message}`, where `row` is the line number (header = line 1).

## Files

| File | Use |
|---|---|
| `valid_sales.csv` | 20 valid rows for `SKU-100` and `SKU-200` (create those products first) |
| `invalid_sales.csv` | 2 valid rows + 8 invalid ones, one for each rejection reason |
