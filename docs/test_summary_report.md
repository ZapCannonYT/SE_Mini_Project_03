# Sprint 2 Test Summary Report

**Report date:** 2026-11-15  
**Build under test:** `main` at `95560fd5faae2ceba771f7c9c900fd1b7017486f`, plus the #34 performance test commit `264e3e982d61917f76ae61d30076ce4bf19f29df`.  
**Execution details:** Case-by-case evidence and reasons for cases not run are recorded in `docs/test_execution_log.md` on branch `docs/35-test-execution-defect-log` (commit `1ad8398`).

## Test execution

| Measure | Result |
|---|---:|
| STP cases in scope | 33 |
| Passed | 22 |
| Failed | 0 |
| Not run | 11 |
| Execution rate | 66.7% (22 / 33) |
| Pass rate among executed cases | 100% (22 / 22) |
| Automated pytest tests | 210 passed, 0 failed, 0 skipped |
| Backend suite duration | 64.24 seconds |

The 11 cases not run were TC-AUD-01, TC-MAINT-01, TC-REL-01, TC-RPT-01, TC-RPT-02, TC-SEC-01 through TC-SEC-05, and TC-UX-01. Reasons are listed per case in the execution log.

## Requirement coverage

| Requirement group | Covered | Total | Coverage |
|---|---:|---:|---:|
| Functional (DFIP-F-001 through DFIP-F-023) | 20 | 23 | 87.0% |
| Non-functional (DFIP-NF-001 through DFIP-NF-005) | 2 | 5 | 40.0% |
| Security (DFIP-SR-001 through DFIP-SR-005) | 0 | 5 | 0.0% |
| **All requirement IDs** | **22** | **33** | **66.7%** |

Covered functional requirements are DFIP-F-001 through DFIP-F-018, DFIP-F-021, and DFIP-F-023. DFIP-F-019, DFIP-F-020, and DFIP-F-022 are not covered by an executed STP case. The executed non-functional requirements are DFIP-NF-001 and DFIP-NF-002. No security requirement has a separately executed, identified STP case in this run. General authorization tests exist but are not counted as security-case execution evidence.

## Performance results

TC-PERF-01 measured 30 sequential requests per endpoint after two warmups. All p90 response times were below the 3-second target.

| Endpoint | Median | p90 | Maximum |
|---|---:|---:|---:|
| `GET /api/products` | 17.797 ms | 20.403 ms | 44.867 ms |
| `GET /api/inventory` | 17.174 ms | 19.570 ms | 22.154 ms |
| `GET /api/sales` | 37.825 ms | 52.982 ms | 212.454 ms |
| `GET /api/dashboard` | 427.461 ms | 450.297 ms | 467.263 ms |

TC-PERF-02 forecasted 12 weeks from 104 weeks of history in 289.994 ms, below its 10-second target. These are local in-process `TestClient` measurements with in-memory SQLite; they do not establish deployed network or browser latency. Full timing and method details are in [performance results](performance_results.md).

## Open defects

One existing Minor defect remains Open: [#61 — Admin cannot create users with an `@dfip.local` email](https://github.com/ZapCannonYT/SE_Mini_Project_03/issues/61). The execution log records that the issue was not reproduced or reclassified during this run.

## Release assessment

The executed cases passed, but the evidence is incomplete: 11 of 33 STP cases were not run, including the security and UI acceptance cases, and one Minor defect remains open. This report does not establish full STP completion or release readiness; those items need review by the QA lead and team.
