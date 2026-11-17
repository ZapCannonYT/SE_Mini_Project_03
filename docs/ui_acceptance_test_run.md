# UI Acceptance Test Run (TC-UX-01, DFIP-NF-004)

**Story:** #40, UI acceptance test run. **Tester:** Rahul Saran Sharma (UI / acceptance tester). **Handed to:** K Preksha (QA lead) for the test execution log (#35) and Test Summary Report (#36).
**Date:** 2026-11-17.

## 1. What was tested

| Item | Value |
|---|---|
| Build | `main` (`0327dc9`) plus the open PRs for #37 (forecast and planning pages), #38 (reports) and #39 (HTTPS and CORS), merged together on a scratch branch. The PRs are not on `main` yet, so these pages were tested on that combined build. |
| Backend | Real FastAPI backend, new SQLite database, `VITE_USE_MOCK` off (no mock data) |
| Data | 3 products (SKU-100, SKU-200, SKU-300), 336 sales rows from `data/samples/make_demo_sales.py` imported through the API, planner and viewer users created by the admin |
| Browser | Built-in Chromium browser pane, viewport 1366 x 768 (common desktop resolution) |
| Role walked through | Planner (non-developer role). The viewer role was checked through the API (403 on forecast creation) and component tests, not in the browser. |
| Transport | The browser pane does not trust the self-signed certificate, so the UI run used plain HTTP on localhost. HTTPS was checked separately (section 4). |

## 2. TC-UX-01 walk-through

Steps: open each screen at 1366 x 768, check it is readable and usable, then trigger validation errors and check the messages are clear.

| Screen | Result | Notes |
|---|---|---|
| Login | Pass | Planner signed in and landed on the dashboard. No demo credentials are shown when the real API is used. |
| Dashboard | Pass | Cards, 30-day trend with forecast, alerts. Current stock 955 equals 50 + 900 + 5 from the product list. Evidence: `ui-acceptance/TC-UX-01-dashboard-planner.jpg`. |
| Products | Pass | Three products listed with safety stock, overstock factor and stock. No create/edit controls for the planner role. |
| Inventory | Pass | Quantities match the product list. |
| Sales | Pass | 336 records, newest first, filters present. |
| Forecasts | Pass | SKU-100, 6 weeks: chart, model, generation time and a table of 6 weekly values. Evidence: `ui-acceptance/TC-UX-01-forecast-chart.jpg`. |
| Planning | Pass | SKU-300: reorder quantity 335, risk Stockout, inputs shown (stock 5, forecast demand 319.08, safety stock 20, factor 1.5). Check: ceil(319.08 + 20 - 5) = 335. Evidence: `ui-acceptance/TC-UX-01-planning-inputs-used.jpg`. |
| Reports | Pass | The recommendation just created appears as one row with the same values. |
| Admin | Pass (access) / Gap | The planner sees "You do not have access to this page". See defect D3 for the admin view. |
| Unknown address | Pass | "Page not found" with a link back to the dashboard. |
| Validation | Pass | Submitting the forecast form empty with horizon 13 shows "Product is required" and "Horizon can be at most 12 weeks" beside the fields. Evidence: `ui-acceptance/TC-UX-01-validation-errors.jpg`. |

**Verdict for TC-UX-01:** Pass with defects D1 and D2 (both fixed in the PRs) and gap D3. Layout at 1366 x 768 is usable; only the desktop size was tried, not phones.

Not done in the browser: the Export CSV button was not clicked (it saves a file); the export is covered by `ReportsPage.test.jsx` and by calling `GET /api/reports/planning/export` directly (section 3).

## 3. Related evidence from the same run

| Test case | Result | Evidence |
|---|---|---|
| TC-DASH-01 | Pass | Dashboard totals matched the products and inventory loaded through the API. |
| TC-PLAN-04 | Pass | Planning page lists the at-risk products from `GET /api/planning/alerts`; the recommendation shows every input used. |
| TC-RPT-01 | Pass | `GET /api/reports/planning` and the Reports page returned the same single row; filters covered by `backend/tests/test_reports.py` and `ReportsPage.test.jsx`. |
| TC-RPT-02 | Pass | `GET /api/reports/planning/export?risk=stockout` returned `planning_report.csv` with the header and the same row as the table (`1,SKU-300,Seasonal Gizmo,...,335,stockout`). |

## 4. TC-SEC-05 (HTTPS), for the security tester

On the same build: `python scripts/make_dev_cert.py`, then the API was started with `uvicorn app.main:app --ssl-keyfile ../certs/dev.key --ssl-certfile ../certs/dev.crt --port 8000`.

- `curl -k https://localhost:8000/health` returned `{"status":"ok"}`; the generated certificate is `CN=localhost` with `DNS:localhost, IP:127.0.0.1`.
- A CORS preflight from `https://localhost:5173` returned `access-control-allow-origin: https://localhost:5173`; a preflight from `https://evil.example.com` returned no CORS header (`backend/tests/test_cors_https.py`).
- `npm run dev:https` served the site over TLS and proxied `/api` to the HTTPS backend.
- Limit: the certificate is self-signed, for development and demos only.

## 4a. Defects raised

| ID | Severity | Found | Status |
|---|---|---|---|
| D1 | Low | The Planning alerts table showed `478.91999999999996` and `966.3000000000001` for forecast demand (raw floating point). | Fixed in the #37 and #38 PRs: quantities are shown with at most 2 decimals (`frontend/src/lib/format.js`); the report API rounds to 2 decimals so the table and CSV agree. |
| D2 | Medium | API timestamps have no timezone (for example `2026-11-17T06:18:37.242246`), so a browser outside UTC would show forecast, recommendation and report times shifted by its offset. | Worked around in the new pages (timestamps read as UTC). Root cause is in the backend response models and also affects Inventory "Last updated"; to be fixed by serialising timestamps with `Z`. |
| D3 | Medium | The Admin screen is still a placeholder ("will appear here"). The admin cannot manage users from the UI although the API exists (DFIP-F-021). | Open. Needs a story or a documented deviation. |
| D4 | Medium | Known defect #61: admin cannot create users with an `@dfip.local` email. | Open (already raised). Worked around with `@example.com` addresses. |

GitHub issues for D2 and D3 have not been created yet; they are listed here for the QA lead's defect log.

## 5. Re-run

1. Follow `docs/run_guide.md` sections 3 to 5, with `VITE_USE_MOCK=false`.
2. Log in as a planner and visit every item in the table in section 2 at 1366 x 768.
3. Trigger the validation errors on Forecasts, Planning and Reports and confirm the messages sit next to the fields.
