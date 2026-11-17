# DFIP - Run Guide

How to install, run and demo DFIP from a fresh clone. Verified on a clean clone of `main` (Windows 11, Python 3.14, Node 26): 253 backend tests and 54 frontend tests passed, and the website ran against the real API.

## 1. Requirements

| Tool | Version |
|---|---|
| Python | 3.12 or newer (CI uses 3.12) |
| Node.js | 20 or newer (CI uses 20) |
| Git | any recent version |

## 2. Get the code

```bash
git clone https://github.com/ZapCannonYT/SE_Mini_Project_03.git
cd SE_Mini_Project_03
```

To run a specific release instead of the latest `main`, check out its tag, e.g. `git checkout v1.0.0`.

## 3. Backend

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # Linux / macOS
pip install -r requirements.txt
copy .env.example .env              # cp .env.example .env on Linux / macOS
```

Open `.env` and set `JWT_SECRET_KEY` to a long random value. This prints one:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

The other settings in `.env` work as they are:

| Setting | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./dfip.db` | SQLite file, created in the folder you start the backend from |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | values in `backend/app/core/config.py` | First admin account, created on the first start. Set your own in `.env` for anything beyond a local demo. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | How long a login lasts |

Check the install, then start the API:

```bash
pytest                              # expect all tests to pass
cd backend
uvicorn app.main:app --reload
```

- Health check: http://localhost:8000/health returns `{"status": "ok"}`
- Interactive API docs (Swagger): http://localhost:8000/docs. Use `POST /api/auth/login`, then the **Authorize** button with the token.

## 4. Frontend

In a second terminal:

```bash
cd frontend
npm ci
copy .env.example .env              # cp on Linux / macOS
```

Choose the data source in `frontend/.env`:

| `VITE_USE_MOCK` | Data comes from | Log in with |
|---|---|---|
| `true` (default) | Built-in mock data, no backend needed | Demo accounts shown on the login page |
| `false` | The real backend on port 8000 | The admin account from the backend `.env` |

```bash
npm run dev                         # http://localhost:5173
```

The dev server forwards `/api` to `http://localhost:8000`, so no CORS setup is needed. Frontend tests and build: `npm test -- --run` and `npm run build`.

## 5. Demo with real data

1. Start the backend (section 3) and the frontend with `VITE_USE_MOCK=false` (section 4), then log in as admin.
2. Generate recent sales history (16 weeks ending yesterday):
   ```bash
   python data/samples/make_demo_sales.py
   ```
3. **Products**: create `SKU-100`, `SKU-200` and `SKU-300`, with some starting stock and a safety stock.
4. **Sales > Import sales from CSV**: upload `data/samples/demo_sales.csv`. On an empty database all 336 rows import.
5. Also upload `data/samples/invalid_sales.csv` to show the row-by-row error report: each bad row is listed with its line number and reason. Its two valid rows may already exist after step 4 and are then reported as duplicates.
6. **Dashboard**: summary cards, the trend chart with a 7-day forecast, and stockout/overstock alerts.
7. Forecasts and reorder plans: `POST /api/forecasts` then `POST /api/planning/recommendations` in Swagger (http://localhost:8000/docs).
8. **Admin**: create a planner and a viewer, then log in as them to show what each role can do.

## 6. Reset

Stop the backend and delete `dfip.db` (in the folder you started it from) to start with an empty database. The admin account is created again on the next start.

## 7. Release (Sprint end)

The repo owner tags the release once every Sprint story is merged and `main` is green:

```bash
git checkout main
git pull
git tag -a v1.0.0 -m "Sprint 2 increment"
git push origin v1.0.0
```

The Release workflow re-runs the tests and publishes a GitHub Release with the source bundle, the built frontend and the test reports (`test-results.xml`, `coverage.xml`).

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| Login returns 500 | `JWT_SECRET_KEY` is empty in `.env`; set it and restart the backend |
| Website login fails with `VITE_USE_MOCK=false` | The backend is not running on port 8000 |
| Website shows demo data instead of yours | `frontend/.env` still has `VITE_USE_MOCK=true`; set it to `false` and restart `npm run dev` |
| Dashboard forecast is 0 | No recent sales; import `demo_sales.csv` from step 5 |
| Creating a user with an `@dfip.local` email fails | Known defect #61; use another domain such as `@example.com` |
| `uvicorn: command not found` | Activate the virtual environment first |
