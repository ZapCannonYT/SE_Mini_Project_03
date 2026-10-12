# Detailed Test Cases - Products, Inventory and Sales

For STP section 13 (the four test cases that only appear in the traceability summary). Each one is also automated; the last row of each table names the pytest test.

Common preconditions: API running with a fresh database; tester logged in through `POST /api/auth/login`; the token is sent as `Authorization: Bearer <token>`.

## TC-PROD-01 - Create, view, update and deactivate a product

| Item | Detail |
|---|---|
| Requirement | DFIP-F-004 |
| Priority | High |
| Preconditions | Logged in as **admin**; no product with SKU `SKU-100` exists |
| Test data | `{"sku": "SKU-100", "name": "Steel bolts", "category": "Hardware", "safety_stock": 20, "initial_quantity": 40}` |
| Steps | 1. `POST /api/products` with the test data.<br>2. `GET /api/products`.<br>3. `PUT /api/products/{id}` with `{"name": "Zinc bolts"}`.<br>4. `PATCH /api/products/{id}/deactivate`.<br>5. `GET /api/products`, then `GET /api/products?include_inactive=true`.<br>6. Repeat step 1 with SKU `sku-100`.<br>7. Log in as **planner** and repeat step 1 with SKU `SKU-101`. |
| Expected result | 1. 201; response shows the SKU, `quantity` 40, `overstock_factor` 1.5, `is_active` true.<br>2. The product is in the list.<br>3. 200; name changed, other fields unchanged.<br>4. 200; `is_active` false.<br>5. Default list is empty; list with `include_inactive=true` shows the product.<br>6. 409 `sku_exists` (SKUs are case-insensitive).<br>7. 403 (only admin can create). |
| Automated | `backend/tests/test_products.py` |

## TC-INV-01 - Stored inventory is retrievable

| Item | Detail |
|---|---|
| Requirement | DFIP-F-005 |
| Priority | High |
| Preconditions | Product `SKU-200` created with `initial_quantity` 15 |
| Test data | Product id of `SKU-200` |
| Steps | 1. Log in as **viewer**.<br>2. `GET /api/inventory/{product_id}`.<br>3. `GET /api/inventory`. |
| Expected result | 2. 200; `sku` `SKU-200`, `quantity` 15.<br>3. The list contains `SKU-200` with quantity 15 and no deactivated products. |
| Automated | `backend/tests/test_inventory.py::test_stored_quantity_is_retrievable`, `::test_list_shows_stock_for_active_products_only` |

## TC-SALES-01 - Add a historical sales record

| Item | Detail |
|---|---|
| Requirement | DFIP-F-007 |
| Priority | High |
| Preconditions | Logged in as **planner**; product `SKU-100` exists and is active |
| Test data | `{"product_id": <SKU-100 id>, "sale_date": "2026-09-01", "quantity_sold": 12}` |
| Steps | 1. `POST /api/sales` with the test data.<br>2. Repeat step 1 with `quantity_sold` 5.<br>3. Repeat step 1 with `quantity_sold` -1, then `"abc"`, then `sale_date` `"01/09/2026"`, then a future date.<br>4. Log in as **viewer** and repeat step 1 with date `2026-09-02`. |
| Expected result | 1. 201; response shows `SKU-100`, `2026-09-01`, 12 and who created it.<br>2. 409 `sale_exists` (one record per product per date).<br>3. 422 `validation_error` naming the bad field each time; nothing stored.<br>4. 403. |
| Automated | `backend/tests/test_sales.py` (manual entry tests) |

## TC-SALES-03 - View and filter historical sales

| Item | Detail |
|---|---|
| Requirement | DFIP-F-009 |
| Priority | Medium |
| Preconditions | Sales for `SKU-100` and `SKU-200` on 2026-09-01, 2026-09-05 and 2026-09-10 |
| Test data | `product_id` = SKU-100 id, `from` = 2026-09-02, `to` = 2026-09-10 |
| Steps | 1. Log in as **viewer**.<br>2. `GET /api/sales?product_id=<id>&from=2026-09-02&to=2026-09-10`.<br>3. `GET /api/sales` with no filters.<br>4. `GET /api/sales?from=2026-09-10&to=2026-09-01`. |
| Expected result | 2. 200; exactly the SKU-100 rows for 2026-09-05 and 2026-09-10, oldest first.<br>3. All six rows, oldest first.<br>4. 400 `invalid_date_range`. |
| Automated | `backend/tests/test_sales.py::test_filter_by_product_and_date_range`, `::test_list_without_filters_returns_everything_oldest_first`, `::test_from_after_to_is_rejected` |
