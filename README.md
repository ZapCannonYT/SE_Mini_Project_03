# Demand Forecasting & Inventory Planning System (DFIPS)
Team 03 - SE Mini Project

Uses historical sales and current inventory to forecast product demand, recommend reorder
quantities, and flag stockout/overstock risk. See the SRS, SAD and STP in [`docs/`](docs/).

## Team

| Member | Area |
|---|---|
| Vishnu P | Data & backend core: database, product/inventory/sales APIs, CSV import |
| Sahana K Golabanvi | Security & admin: auth, RBAC, users, audit log; docs coordinator |
| K Preksha | Forecasting & planning engine; QA lead |
| Rahul Saran Sharma | Frontend, dashboard, reports, deployment |

## Project layout

```
backend/app/
  main.py        FastAPI entry point
  core/          config, database, security helpers
  api/           REST endpoints (presentation of the API)
  services/      business logic (application layer)
  analytics/     preprocessing, forecasting, planning (analytics layer)
  models/        SQLAlchemy tables (data layer)
  schemas/       Pydantic request/response models
backend/tests/   pytest tests
frontend/        web UI
data/samples/    sample CSV files for import/testing
docs/            SRS, SAD, STP
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
copy .env.example .env          # cp on Linux/macOS
pytest
```

Run the API from the `backend/` folder:

```bash
uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs for the interactive API docs.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the branch, commit and PR rules.
