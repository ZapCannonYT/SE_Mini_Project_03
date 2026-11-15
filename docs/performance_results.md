# Performance Test Results

**Executed:** 2026-11-15  
**Build:** `main` at `95560fd5faae2ceba771f7c9c900fd1b7017486f` plus the uncommitted #34 performance test  
**Environment:** Windows 11, Python 3.14.8, FastAPI `TestClient`, in-memory SQLite  
**Outcome:** Both performance test cases passed.

## TC-PERF-01 - Data retrieval and dashboard

The test seeded 12 catalog products with 56 weekly observations each, plus a forecast sample, then warmed each endpoint twice and measured 30 sequential requests. The p90 is calculated using the nearest-rank method. The acceptance limit is under 3 seconds for at least 90% of requests.

| Endpoint | Requests | Median (ms) | p90 (ms) | Maximum (ms) | Result |
|---|---:|---:|---:|---:|---|
| `GET /api/products` | 30 | 17.797 | 20.403 | 44.867 | Pass |
| `GET /api/inventory` | 30 | 17.174 | 19.570 | 22.154 | Pass |
| `GET /api/sales` | 30 | 37.825 | 52.982 | 212.454 | Pass |
| `GET /api/dashboard` | 30 | 427.461 | 450.297 | 467.263 | Pass |

All measured p90 values were below the 3,000 ms limit.

## TC-PERF-02 - Single-product forecast

The test generated one 12-week forecast from 104 weekly observations for a single product. The forecast endpoint completed in **289.994 ms**, below the 10,000 ms limit: **Pass**.

## Method and evidence

- Measurements use the automated test `backend/tests/test_performance.py` and are captured in test output with the test report.
- The tests use synthetic, in-memory records and include API handling, database access, forecasting, and response serialization.
- These are local in-process measurements; they do not include network, TLS, browser rendering, or deployment latency. Repeat the same checks against the deployed environment before making a production latency claim.
- The repository CI workflow already produces `test-results.xml` and `coverage.xml` and uploads them as the `test-reports` artifact for each push or pull request run.
