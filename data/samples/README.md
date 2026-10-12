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

- The header is required; column order does not matter and extra columns are ignored.
- UTF-8 (Excel's "CSV UTF-8" is fine), max 2 MB.
- One row per product per date. Rows that repeat an earlier row in the file, or a date already stored, are rejected.
- Valid rows are saved; every invalid row is reported with its line number (header = line 1) and the reason.

## Files

| File | Use |
|---|---|
| `valid_sales.csv` | 20 valid rows for `SKU-100` and `SKU-200` (create those products first) |
| `invalid_sales.csv` | 2 valid rows + 8 invalid ones covering each rejection reason |
| `sales_patterns.csv` | ~3 years of daily sales for `SKU-NORMAL`, `SKU-INCREASING`, `SKU-SEASONAL`, `SKU-SPARSE` - for forecasting demos |
