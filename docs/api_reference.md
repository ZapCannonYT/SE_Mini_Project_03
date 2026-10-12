# DFIP - REST API Reference

Generated from the FastAPI app (`app.openapi()`); interactive version at `http://localhost:8000/docs`.

All endpoints except login and `/health` need `Authorization: Bearer <token>` from `POST /api/auth/login`.
Errors from products, inventory and sales use `{"code", "message", "details"}`; validation errors (422) list each field.

## Endpoints

| Method | Path | Purpose | Request body | Success response |
|---|---|---|---|---|
| POST | `/api/auth/login` | Login | `LoginRequest` | 200 `LoginResponse` |
| POST | `/api/auth/logout` | Logout | - | 200  |
| POST | `/api/products` | Create a product/SKU with its starting stock (DFIP-F-004). Admin only. | `ProductCreate` | 201 `ProductOut` |
| GET | `/api/products` | List Products | query: `include_inactive` | 200 list of `ProductOut` |
| GET | `/api/products/{product_id}` | Get Product | - | 200 `ProductOut` |
| PUT | `/api/products/{product_id}` | Update product details; only the fields sent are changed. Admin only. | `ProductUpdate` | 200 `ProductOut` |
| PATCH | `/api/products/{product_id}/deactivate` | Hide a product from normal lists and planning without deleting its history. Admin only. | - | 200 `ProductOut` |
| GET | `/api/inventory` | Current stock for every active product (DFIP-F-005). | - | 200 list of `InventoryOut` |
| GET | `/api/inventory/{product_id}` | Get Stock | - | 200 `InventoryOut` |
| PUT | `/api/inventory/{product_id}` | Set the current stock quantity (DFIP-F-006). Admin or planner. | `InventoryUpdate` | 200 `InventoryOut` |
| POST | `/api/sales` | Record units sold for one product on one date (DFIP-F-007). Admin or planner. | `SalesCreate` | 201 `SalesOut` |
| GET | `/api/sales` | Historical sales filtered by product and date range (DFIP-F-009). | query: `product_id`, `from`, `to` | 200 list of `SalesOut` |
| POST | `/api/sales/import` | Import historical sales from CSV (DFIP-F-008). Valid rows are saved; invalid rows are listed by line number. | CSV file (`file`) | 200 `ImportResult` |
| GET | `/health` | Health | - | 200 object |

## Request / response schemas

### ImportResult

| Field | Type | Required | Notes |
|---|---|---|---|
| `total_rows` | integer | yes |  |
| `imported` | integer | yes |  |
| `rejected` | integer | yes |  |
| `errors` | list of `ImportRowError` | yes |  |

### ImportRowError

| Field | Type | Required | Notes |
|---|---|---|---|
| `row` | integer | yes | Line number in the CSV file (the header is line 1). |
| `error` | string | yes |  |

### InventoryOut

| Field | Type | Required | Notes |
|---|---|---|---|
| `product_id` | integer | yes |  |
| `sku` | string | yes |  |
| `name` | string | yes |  |
| `quantity` | integer | yes |  |
| `updated_at` | string or null | yes |  |
| `updated_by` | integer or null | yes |  |

### InventoryUpdate

| Field | Type | Required | Notes |
|---|---|---|---|
| `quantity` | integer | yes | >= 0.0; Whole number of units on hand (>= 0). |

### LoginRequest

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string | yes |  |
| `password` | string | yes |  |

### LoginResponse

| Field | Type | Required | Notes |
|---|---|---|---|
| `access_token` | string | yes |  |
| `token_type` | string | no | default bearer |
| `role` | string | yes |  |

### ProductCreate

| Field | Type | Required | Notes |
|---|---|---|---|
| `sku` | string | yes | pattern ^[A-Za-z0-9][A-Za-z0-9_-]{0,49}$; Letters, digits, '-' or '_' (max 50). Cannot be changed later. |
| `name` | string | yes | max length 200 |
| `category` | string or null | no |  |
| `unit` | string | no | max length 20; default unit |
| `safety_stock` | integer | no | >= 0.0; default 0 |
| `overstock_factor` | number | no | > 0.0; <= 10.0; default 1.5 |
| `initial_quantity` | integer | no | >= 0.0; default 0; Starting stock for the new product. |

### ProductOut

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | integer | yes |  |
| `sku` | string | yes |  |
| `name` | string | yes |  |
| `category` | string or null | yes |  |
| `unit` | string | yes |  |
| `safety_stock` | integer | yes |  |
| `overstock_factor` | number | yes |  |
| `is_active` | boolean | yes |  |
| `created_at` | string | yes |  |
| `quantity` | integer | yes | Current stock on hand. |

### ProductUpdate

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string or null | no |  |
| `category` | string or null | no |  |
| `unit` | string or null | no |  |
| `safety_stock` | integer or null | no |  |
| `overstock_factor` | number or null | no |  |

### SalesCreate

| Field | Type | Required | Notes |
|---|---|---|---|
| `product_id` | integer | yes | > 0.0 |
| `sale_date` | string | yes | YYYY-MM-DD, not in the future. |
| `quantity_sold` | integer | yes | >= 0.0; Whole number of units sold (>= 0). |

### SalesOut

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | integer | yes |  |
| `product_id` | integer | yes |  |
| `sku` | string | yes |  |
| `sale_date` | string | yes |  |
| `quantity_sold` | integer | yes |  |
| `created_by` | integer or null | yes |  |
| `created_at` | string | yes |  |
