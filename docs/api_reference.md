# DFIP - REST API Reference

Interactive version (Swagger UI) at `http://localhost:8000/docs` while the backend is running.

All endpoints except login and `/health` need `Authorization: Bearer <token>` from `POST /api/auth/login`.

## Endpoints

| Method | Path | Purpose | Who | Request | Success |
|---|---|---|---|---|---|
| POST | `/api/auth/login` | Log in, get a token | anyone | `{"email", "password"}` | 200 `{"access_token", "token_type", "role"}` |
| POST | `/api/auth/logout` | Log out (client drops the token) | anyone | - | 200 |
| POST | `/api/products` | Create a product/SKU with its starting stock (DFIP-F-004) | admin | `ProductCreate` | 201 `ProductOut` |
| GET | `/api/products` | List active products | all roles | query `include_inactive` (default false) | 200 list of `ProductOut` |
| GET | `/api/products/{product_id}` | One product | all roles | - | 200 `ProductOut` |
| PUT | `/api/products/{product_id}` | Update details; only the fields sent change | admin | `ProductUpdate` | 200 `ProductOut` |
| PATCH | `/api/products/{product_id}/deactivate` | Hide from lists and planning, keep history | admin | - | 200 `ProductOut` |
| GET | `/api/inventory` | Current stock for every active product (DFIP-F-005) | all roles | - | 200 list of `InventoryOut` |
| GET | `/api/inventory/{product_id}` | Stock for one product | all roles | - | 200 `InventoryOut` |
| PUT | `/api/inventory/{product_id}` | Set current stock (DFIP-F-006) | admin, planner | `InventoryUpdate` | 200 `InventoryOut` |
| POST | `/api/sales` | Record units sold for one product on one date (DFIP-F-007) | admin, planner | `SalesCreate` | 201 `SalesOut` |
| GET | `/api/sales` | Sales history, newest first (DFIP-F-009) | all roles | query `product_id`, `start_date`, `end_date` (all optional, dates inclusive) | 200 list of `SalesOut` |
| POST | `/api/sales/import` | Import sales from a CSV file (DFIP-F-008) | admin, planner | multipart field `file` | 200 `ImportResult` |
| POST | `/api/forecasts` | Generate and store a weekly or monthly forecast (DFIP-F-010..012) | admin, planner | `{"product_id", "horizon", "unit"}` | 201 `ForecastOut` |
| GET | `/api/forecasts` | List stored forecasts; optionally filter by product | all roles | query `product_id` | 200 list of `ForecastOut` |
| GET | `/api/forecasts/{forecast_id}` | Retrieve one forecast and its points | all roles | - | 200 `ForecastOut` |
| POST | `/api/planning/recommendations` | Calculate and store reorder/risk result (DFIP-F-013..016) | admin, planner | `{"forecast_id", "current_stock?", "safety_stock?", "overstock_factor?"}` | 201 `RecommendationOut` |
| GET | `/api/planning/recommendations/{recommendation_id}` | Retrieve a recommendation and all inputs used | all roles | - | 200 `RecommendationOut` |
| GET | `/api/planning/alerts` | List active products currently at stockout or overstock risk | all roles | - | 200 list of `PlanningAlertOut` |
| GET | `/api/dashboard` | Dashboard totals, active-product plans and 30-day actual/7-day forecast trend (DFIP-F-017/F-018) | all roles | - | 200 `DashboardOut` |
| GET | `/health` | Liveness check | anyone | - | 200 |

## Errors

Product, inventory and sales errors share one JSON shape (SAD 4.4):

```json
{"code": "validation_error", "message": "Some fields are missing or invalid.", "details": [{"field": "quantity", "message": "Input should be greater than or equal to 0"}]}
```

Forecast horizon errors use 400 `invalid_forecast_request`; history shorter than 8 weekly or monthly periods uses 422 `insufficient_history`. Missing forecast or recommendation ids return 404 `forecast_not_found` or `recommendation_not_found`.

| Status | `code` | When |
|---|---|---|
| 401 | - | Missing, invalid or expired token |
| 403 | - | Role not allowed for this endpoint |
| 404 | `product_not_found` | No product with that id |
| 409 | `sku_exists` | SKU already used (SKUs are case-insensitive) |
| 409 | `product_inactive` | Changing stock of, or adding a sale for, a deactivated product |
| 409 | `sale_exists` | The product already has a sales record on that date |
| 413 | `file_too_large` | CSV import over 2 MB |
| 422 | `invalid_csv` | CSV import that is empty, not UTF-8, or whose header is not exactly `sku,date,quantity_sold`; nothing is stored |
| 422 | `validation_error` | Missing, unknown, negative or non-numeric fields, bad or future dates, or `start_date` after `end_date`; `details` lists each field |

## Schemas

### ProductCreate

| Field | Type | Required | Notes |
|---|---|---|---|
| `sku` | string | yes | Letters, digits, `-` or `_`, max 50. Cannot be changed later. |
| `name` | string | yes | 1-200 characters |
| `category` | string or null | no | max 100 |
| `unit` | string | no | default `unit` |
| `safety_stock` | integer | no | >= 0, default 0 |
| `overstock_factor` | number | no | >= 1 and <= 10, default 1.5 |
| `initial_quantity` | integer | no | >= 0, default 0; starting stock |

Unknown fields are rejected with 422.

### ProductUpdate

Any subset of `name`, `category`, `unit`, `safety_stock`, `overstock_factor` (same rules as above). `sku` cannot be changed, and `name`/`unit` cannot be set to null.

### ProductOut

`id`, `sku`, `name`, `category`, `unit`, `safety_stock`, `overstock_factor`, `is_active`, `created_at`, `quantity` (current stock).

### InventoryUpdate

| Field | Type | Required | Notes |
|---|---|---|---|
| `quantity` | integer | yes | Whole number >= 0; `"10"` or `1.5` are rejected |

### InventoryOut

`product_id`, `sku`, `name`, `quantity`, `updated_at`, `updated_by` (user id of the last change).

### SalesCreate

| Field | Type | Required | Notes |
|---|---|---|---|
| `product_id` | integer | yes | An active product |
| `sale_date` | string | yes | `YYYY-MM-DD`, not in the future |
| `quantity_sold` | integer | yes | Whole number >= 0 |

### SalesOut

`id`, `product_id`, `sku`, `name`, `sale_date`, `quantity_sold`, `created_by` (user id of whoever recorded or imported it), `created_at`.

### ImportResult

```json
{"imported": 2, "rejected": [{"row": 3, "message": "Quantity sold cannot be negative"}]}
```

Valid rows are saved together in one transaction; `row` is the line number in the file (header = line 1). File format and sample files: `data/samples/README.md`.

### ForecastCreate and ForecastOut

`ForecastCreate` requires a positive `product_id`, a supported `horizon`, and `unit` (`week` or `month`). Weekly horizons are 1–12 periods and monthly horizons are 1–6. Forecasts use historical sales records for the selected active product and the saved `minimum_history_periods` setting (default 8); insufficient history returns 422. `ForecastOut` includes stored model metadata and ordered points (`period_start`, `predicted_qty`).

### RecommendationCreate and RecommendationOut

`RecommendationCreate` requires a `forecast_id`. `current_stock`, `safety_stock`, and `overstock_factor` are optional overrides. For safety stock and overstock factor, explicit request values take precedence over the saved global defaults (`default_safety_stock`, `default_overstock_factor`); when no global value exists, the product values are used. `RecommendationOut` returns the complete input snapshot (`current_stock`, `forecast_demand`, `safety_stock`, `overstock_factor`), `reorder_qty`, `risk`, and associated IDs. Alerts use the saved global defaults when available, otherwise each product's values, and include only non-`none` risks.

### DashboardOut

The authenticated dashboard returns `generated_at`, `horizon_days` (7), totals, active-product `items`, and a `trend` with 30 past daily actuals followed by 7 future daily forecasts. The weekly forecasting engine uses the saved `minimum_history_periods` setting (default 8); shorter histories use the frontend's trailing-28-day average, and no sales history yields a zero forecast. Planning values follow the saved global defaults when present and otherwise use product values.

## User Administration (DFIP-F-021)

All endpoints below require an admin Bearer token.

| Method | Path | Purpose | Who | Request | Success |
|---|---|---|---|---|---|
| GET | `/api/users` | List all users | admin | - | 200 list of `UserOut` |
| POST | `/api/users` | Create a user | admin | `UserCreate` | 201 `UserOut` |
| PATCH | `/api/users/{user_id}/role` | Change a user's role | admin | `{"role": "admin\|planner\|viewer"}` | 200 `UserOut` |
| PATCH | `/api/users/{user_id}/deactivate` | Deactivate a user | admin | - | 200 `UserOut` |

### UserCreate

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | 1–100 characters |
| `email` | string | yes | Valid email; must be unique |
| `password` | string | yes | 8–128 characters |
| `role` | string | yes | `admin`, `planner`, or `viewer` |

### UserOut

`id`, `name`, `email`, `role`, `is_active`, `created_at`.

Passwords and password hashes are never returned.

### Administration rules

- Only admins can access user administration endpoints.
- Admins cannot change their own role.
- Admins cannot deactivate their own account.
- Role changes apply on the next request.
- Deactivated users cannot access protected endpoints.
