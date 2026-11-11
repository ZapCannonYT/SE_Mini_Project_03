# Test Cases - End-to-End, Reliability and Input Validation (#27)

Detailed steps for the STP system-test flow, TC-REL-01 and TC-SEC-04. Each case is also automated; the last row names the pytest file. Results go into the test execution log (#35) and failures become `[Defect]` issues.

Common preconditions: backend running on a fresh database with `.env` set up (`JWT_SECRET_KEY` set); seeded admin from `.env` (`ADMIN_EMAIL` / `ADMIN_PASSWORD`); requests send `Authorization: Bearer <token>` from `POST /api/auth/login`. Sample files are in `data/samples/`.

## E2E-01 - Login, set up data, import sales, view history

| Item | Detail |
|---|---|
| Requirements | DFIP-F-001, F-004 to F-009, F-021, SR-004 |
| Priority | High |
| Steps | 1. Log in as admin.<br>2. `POST /api/users`: planner `pat@example.com` and viewer `val@example.com`.<br>3. `POST /api/products`: `SKU-100` (stock 40) and `SKU-200` (stock 120), safety stock 10.<br>4. Log in as the planner; `POST /api/sales/import` with `valid_sales.csv`.<br>5. Planner adds one more day by hand (`POST /api/sales`) and sets SKU-100 stock to 35.<br>6. Log in as the viewer; `GET /api/sales?product_id=<SKU-100>&start_date=2026-09-01` and `GET /api/inventory`.<br>7. Viewer tries `POST /api/sales`.<br>8. Planner logs out; call `GET /api/sales` with no token. |
| Expected result | 2-3. 201 each.<br>4. `{"imported": 20, "rejected": []}`.<br>5. 201, then 200.<br>6. 11 rows for SKU-100, newest first; stock SKU-100 = 35, SKU-200 = 120.<br>7. 403.<br>8. 200, then 401. |
| Automated | `backend/tests/test_e2e.py::test_admin_sets_up_data_and_planner_imports_sales` |

## E2E-02 - Forecast, plan and report (after #33 and #38)

| Item | Detail |
|---|---|
| Requirements | DFIP-F-010 to F-020 |
| Priority | High |
| Preconditions | E2E-01 completed |
| Steps | 1. Planner generates a forecast for SKU-100 and SKU-200.<br>2. Planner opens the planning recommendations.<br>3. Any role opens the dashboard.<br>4. Planner exports the planning report as CSV. |
| Expected result | 1. A forecast for each product over the chosen horizon.<br>2. Reorder quantity = `max(0, ceil(forecast + safety_stock - stock))`; risk stockout / overstock / none.<br>3. Totals and alerts match step 2.<br>4. CSV rows match step 2. |
| Automated | Added to `backend/tests/test_e2e.py` once the endpoints are merged. |

## E2E-03 - Each role can only do what it is allowed to

| Item | Detail |
|---|---|
| Requirements | DFIP-SR-004 |
| Steps | As admin, planner and viewer: create a product, set stock, add a sale, list users. |
| Expected result | Admin: all allowed. Planner: stock and sales only. Viewer: read only (403 on every write). |
| Automated | `backend/tests/test_e2e.py::test_roles_see_only_what_they_may_change` |

## TC-REL-01 - Committed data survives a restart

| Item | Detail |
|---|---|
| Requirement | DFIP-NF-003 |
| Priority | High |
| Preconditions | Backend on a file database (`DATABASE_URL=sqlite:///./dfip.db`) |
| Steps | 1. As admin: create three products, rename one, set its stock to 25, deactivate another, add one sale by hand, import a 2-row CSV, create a planner.<br>2. Read back products (including inactive), inventory, sales and users.<br>3. Stop the backend normally and start it again.<br>4. Log in again and repeat step 2.<br>5. Log in as the planner created in step 1.<br>6. Repeat on a fresh database, sending only rejected requests (bad CSV header, negative quantity, non-numeric stock), restart, and check. |
| Expected result | 4. Identical to step 2: new name, stock 25, product still deactivated, 3 sales rows, planner present, and only one seeded admin.<br>5. Login works.<br>6. No sales stored and stock unchanged. |
| Automated | `backend/tests/test_reliability.py` (restart = close every database connection and start the app again on the same file) |

## TC-SEC-04 - Malformed and malicious-looking input

| Item | Detail |
|---|---|
| Requirement | DFIP-SR-004 |
| Priority | High |
| Test data | `<script>alert('x')</script>`, `Robert'); DROP TABLE products;--`, `' OR '1'='1`, `=HYPERLINK("http://evil")`, `1 OR 1=1`, malformed JSON |
| Steps | 1. Create a product whose name and category are each test string.<br>2. Create a product whose SKU is each test string.<br>3. Use the strings as `product_id`, `start_date` and `end_date` filters on `GET /api/sales`, and as ids in URLs.<br>4. Log in with `' OR '1'='1` as email and password.<br>5. Import a CSV whose SKU, date and quantity cells contain the strings, plus one valid row.<br>6. Send non-JSON, an array, truncated JSON and `null` to `POST /api/sales`.<br>7. Create users with a script name, a SQL-like role or email, or an extra `is_admin` field.<br>8. Check every error response for stack traces or SQL. |
| Expected result | 1. 201; text stored and returned exactly as sent, as JSON (never run); other tables untouched.<br>2-3. 422, nothing stored.<br>4. 401, no token.<br>5. Only the valid row imported; every other row rejected with its line number.<br>6-7. 422, nothing stored.<br>8. No traceback, SQLAlchemy or SQL text. |
| Automated | `backend/tests/test_input_validation.py` |

## Defects raised

| Defect | Found by | Status |
|---|---|---|
| #61 Admin cannot create users with an `@dfip.local` email | TC-REL-01 | Open (owner: #18 user administration) |
