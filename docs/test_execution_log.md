# Sprint 2 Test Execution and Defect Log

**Executed:** 2026-11-15  
**Source:** latest local `main` (`95560fd5faae2ceba771f7c9c900fd1b7017486f`) plus the #34 performance test branch (`264e3e982d61917f76ae61d30076ce4bf19f29df`).  
**Environment:** Windows 11, Python 3.14.8, pytest, FastAPI `TestClient`, in-memory SQLite.  
**Overall backend run:** 210 passed, 0 failed, 0 skipped in 64.24 s. Eight dependency deprecation warnings were emitted.  
**Execution meaning:** Pass means the corresponding automated test coverage ran and passed in this backend run. Not Run means no execution evidence for that STP case was available; related tests are not counted as that case unless explicitly identified.

## Execution log

| STP test case | Result | Evidence / reason |
|---|---|---|
| TC-ADM-01 | Pass | `backend/tests/test_users.py` — admin user creation and validation tests. |
| TC-AUD-01 | Not Run | No audit-log test or audit-log implementation was available in this `main` snapshot. |
| TC-AUTH-01 | Pass | `backend/tests/test_auth.py` — successful login. |
| TC-AUTH-02 | Pass | `backend/tests/test_auth.py` — incorrect-password and unknown-user login rejection. |
| TC-AUTH-03 | Pass | `backend/tests/test_auth.py` — logout and authentication behavior. |
| TC-CFG-01 | Pass | `backend/tests/test_settings.py` and `backend/tests/test_config.py` — settings/configuration behavior. |
| TC-DASH-01 | Pass | `backend/tests/test_dashboard_api.py` — populated and empty dashboard responses. |
| TC-DASH-02 | Pass | `backend/tests/test_dashboard_api.py` — dashboard trend, sparse-history, and authentication behavior. |
| TC-FCST-01 | Pass | `backend/tests/test_forecasting.py` — forecast horizon and `backend/tests/test_forecasts_api.py` API coverage. |
| TC-FCST-02 | Pass | `backend/tests/test_forecasting.py` and `backend/tests/test_preprocessing.py` — insufficient history handling. |
| TC-FCST-03 | Pass | `backend/tests/test_forecasting.py` — forecast result metadata. |
| TC-INV-01 | Pass | `backend/tests/test_inventory.py` — inventory is retrievable. |
| TC-INV-02 | Pass | `backend/tests/test_inventory.py` — planner update persistence and invalid quantity rejection. |
| TC-MAINT-01 | Not Run | The STP maintenance test was not separately executed or recorded in the backend suite. |
| TC-PERF-01 | Pass | `backend/tests/test_performance.py` — 30 measured requests per endpoint; p90 below 3 seconds. See [performance results](performance_results.md). |
| TC-PERF-02 | Pass | `backend/tests/test_performance.py` — 104-week single-product forecast below 10 seconds. See [performance results](performance_results.md). |
| TC-PLAN-01 | Pass | `backend/tests/test_planning.py` and `backend/tests/test_planning_api.py` — recommendation calculation and API response. |
| TC-PLAN-02 | Pass | `backend/tests/test_planning.py` — planning risk classification. |
| TC-PLAN-03 | Pass | `backend/tests/test_planning.py` and `backend/tests/test_planning_api.py` — recommendation inputs/defaults. |
| TC-PLAN-04 | Pass | `backend/tests/test_planning_api.py` — planning alerts and alert defaults. |
| TC-PROD-01 | Pass | `backend/tests/test_products.py` — product creation and listing. |
| TC-REL-01 | Not Run | The end-to-end reliability scenario was not executed in this backend-only run. |
| TC-RPT-01 | Not Run | No report-generation test was available in this `main` snapshot. |
| TC-RPT-02 | Not Run | No report-filter/export test was available in this `main` snapshot. |
| TC-SALES-01 | Pass | `backend/tests/test_sales.py` — manual sale entry and validation. |
| TC-SALES-02 | Pass | `backend/tests/test_sales.py` — CSV import scenarios. |
| TC-SALES-03 | Pass | `backend/tests/test_sales.py` — sales filtering and listing. |
| TC-SEC-01 | Not Run | The named STP security scenario was not separately executed or recorded; general authorization tests do not count as this case. |
| TC-SEC-02 | Not Run | The named STP security scenario was not separately executed or recorded; general authorization tests do not count as this case. |
| TC-SEC-03 | Not Run | The named STP security scenario was not separately executed or recorded; general authorization tests do not count as this case. |
| TC-SEC-04 | Not Run | The named STP security scenario was not separately executed or recorded; general authorization tests do not count as this case. |
| TC-SEC-05 | Not Run | The named STP security scenario was not separately executed or recorded; general authorization tests do not count as this case. |
| TC-UX-01 | Not Run | No browser/UI acceptance run was performed. |

**Totals:** 22 passed, 0 failed, 11 not run, 33 total STP cases. Execution rate: 66.7%. Pass rate among executed cases: 100%.

## Defect log

| Defect | Severity | Status | Affected test / evidence |
|---|---|---|---|
| [#61 — Admin cannot create users with an `@dfip.local` email](https://github.com/ZapCannonYT/SE_Mini_Project_03/issues/61) | Minor | Open | Reported against TC-REL-01. Existing GitHub issue; not reproduced or reclassified in this run. |

## CI evidence

The repository CI workflow runs pytest with JUnit XML and coverage output, then uploads `test-results.xml` and `coverage.xml` as the `test-reports` artifact. This local run produced 210 passing pytest cases; its temporary JUnit file was not retained in the repository. A future CI run on the pull request will provide the downloadable artifact.
