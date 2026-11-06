# DFIP Frontend

Web UI / Dashboard for the Demand Forecasting & Inventory Planning system (SAD 3.4): login, data-entry forms, forecast and planning views, alerts and reports.

## Stack

- Vite + React (plain JavaScript)
- react-router-dom v6
- Vitest, Testing Library, jsdom

## Getting started

```
npm install
npm run dev
```

The app is served at http://localhost:5173. The dev server proxies `/api` and `/health` to the backend on http://localhost:8000 (the backend has no CORS configuration, so always go through the proxy).

## Mock mode vs real API

Mock mode is ON unless `VITE_USE_MOCK` is exactly `false`. In mock mode no network calls are made; an in-memory fake backend (`src/api/mock.js`) answers every request with about 250ms latency and mirrors the real API's roles, validation rules and error shapes. Data resets on page reload.

To use the real backend, copy the example env file and turn mock mode off:

```
cp .env.example .env.local
# edit .env.local: VITE_USE_MOCK=false
```

`VITE_API_BASE_URL` stays empty to use the same origin via the Vite proxy.

### Demo mock accounts

These exist only in the in-browser mock and are not real credentials.

| Email | Role |
| --- | --- |
| admin@dfip.local | admin |
| planner@dfip.local | planner |
| viewer@dfip.local | viewer |

Mock password for all three: `password123`.

## Scripts

- `npm run dev` - start the dev server
- `npm run build` - production build into `dist/`
- `npm run preview` - serve the production build
- `npm test` - run the Vitest suite (watch mode; use `npm test -- --run` for a single run)

## Folder layout

```
frontend/
  index.html
  vite.config.js         Vite, dev proxy and Vitest config
  .env.example
  src/
    main.jsx             entry point
    App.jsx              routes
    styles.css           global styles and shared classes
    api/
      client.js          fetch wrapper, ApiError, mock switch
      endpoints.js       named API functions
      mock.js            in-memory mock backend (route table)
    auth/
      storage.js         localStorage helpers
      AuthContext.jsx    AuthProvider, useAuth, RequireAuth, hasRole
    components/
      Layout.jsx         sidebar, header, outlet
      FormField.jsx      label, control and error text
      ProductForm.jsx    product create/edit form
    pages/
      LoginPage.jsx
      PlaceholderPage.jsx
      NotFoundPage.jsx
      ProductsPage.jsx
      InventoryPage.jsx
      SalesPage.jsx
    test/
      setup.js           Vitest setup (jest-dom, mock reset)
```

## Data screens

| Screen | Route | Admin | Planner | Viewer |
| --- | --- | --- | --- | --- |
| Products (DFIP-F-004) | `/products` | view, create, edit, deactivate | view | view |
| Inventory (DFIP-F-005/F-006) | `/inventory` | view, update quantities | view, update quantities | view |
| Sales (DFIP-F-007/F-008/F-009) | `/sales` | view, filter, add, CSV import | view, filter, add, CSV import | view, filter |

Write controls are hidden for roles that cannot use them; the API enforces the same rules. Forms validate on the client and show per-field messages, and server 422/409 errors are mapped back onto the fields.

### Provisional sales API

The sales backend lands in Sprint 2, so the `/api/sales` endpoints are provisional. They are implemented only in the mock (`src/api/mock.js`) and in `src/api/endpoints.js`, and may change when the backend story lands. Assumed contract:

- `GET /api/sales?product_id=&start_date=&end_date=` (any role) returns a list of `{id, product_id, sku, name, sale_date, quantity_sold}`, newest date first. Dates are `YYYY-MM-DD`. 422 if a date is invalid or start is after end.
- `POST /api/sales` (admin, planner) with `{product_id, sale_date, quantity_sold}` returns 201 with the record. 422 `validation_error` for missing or unknown fields, non-integer or negative quantity, bad or future date; 404 `product_not_found`; 409 `sale_exists` when the product already has a record on that date.
- `POST /api/sales/import` (admin, planner) takes multipart form data with a `file` field (CSV). In mock mode the client reads the file text and sends it as the body. The header must be exactly `sku,date,quantity_sold` (case-insensitive); otherwise (or if the file is empty) 422 `{code: "invalid_csv", message}` and nothing is stored. Valid rows are stored and invalid rows (unknown SKU, bad or future date, non-integer or negative quantity, duplicate product and date in the file or in stored data) are reported. Response 200 `{imported: n, rejected: [{row, message}]}` where `row` is the 1-based line number including the header.

The mock seeds 60 days of deterministic sales history for the active products, ending yesterday.
