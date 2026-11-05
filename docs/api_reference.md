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
| GET | `/health` | Liveness check | anyone | - | 200 |

## Errors

Product and inventory errors share one JSON shape (SAD 4.4):

```json
{"code": "validation_error", "message": "Some fields are missing or invalid.", "details": [{"field": "quantity", "message": "Input should be greater than or equal to 0"}]}
```

| Status | `code` | When |
|---|---|---|
| 401 | - | Missing, invalid or expired token |
| 403 | - | Role not allowed for this endpoint |
| 404 | `product_not_found` | No product with that id |
| 409 | `sku_exists` | SKU already used (SKUs are case-insensitive) |
| 409 | `product_inactive` | Changing stock of a deactivated product |
| 422 | `validation_error` | Missing, unknown, negative or non-numeric fields; `details` lists each field |

## Schemas

### ProductCreate

| Field | Type | Required | Notes |
|---|---|---|---|
| `sku` | string | yes | Letters, digits, `-` or `_`, max 50. Cannot be changed later. |
| `name` | string | yes | 1-200 characters |
| `category` | string or null | no | max 100 |
| `unit` | string | no | default `unit` |
| `safety_stock` | integer | no | >= 0, default 0 |
| `overstock_factor` | number | no | > 0 and <= 10, default 1.5 |
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