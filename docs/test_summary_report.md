# Sprint 2 Test Summary Report

**Report date:** 2026-11-16 
**Build under test:** Latest main commit: e6d4858, with the performance and security test evidence referenced in docs/test_execution_log.md. 
**Execution details:** Case-by-case execution evidence and reasons for cases not run are recorded in docs/test_execution_log.md (execution date: 2026-11-16).

## Test execution

| Measure | Result |
|---|---:|
| STP cases in scope | 33 |
| Passed | 25 |
| Failed | 0 |
| Not run | 8 |
| Execution rate | 75.8% (25 / 33) |
| Pass rate among executed cases | 100% (25 / 25) |
| Automated pytest tests | 210 passed, 0 failed, 0 skipped |
| Backend suite duration | 64.24 seconds |

The 8 cases not run were TC-AUD-01, TC-MAINT-01, TC-REL-01, TC-RPT-01, TC-RPT-02, TC-SEC-04, TC-SEC-05, and TC-UX-01. Reasons are recorded per case in `docs/test_execution_log.md`.

## Requirement coverage

| Requirement group | Covered | Total | Coverage |
|---|---:|---:|---:|
| Functional (DFIP-F-001 through DFIP-F-023) | 20 | 23 | 87.0% |
| Non-functional (DFIP-NF-001 through DFIP-NF-005) | 2 | 5 | 40.0% |
| Security (DFIP-SR-001 through DFIP-SR-005) | 3 | 5 | 60.0% |
| **All requirement IDs** | **25** | **33** | **75.8%** |

Covered functional requirements are DFIP-F-001 through DFIP-F-018, DFIP-F-021, and DFIP-F-023. DFIP-F-019, DFIP-F-020, and DFIP-F-022 are not covered by an executed STP case.

The executed non-functional requirements are DFIP-NF-001 and DFIP-NF-002.

The executed security requirements are DFIP-SR-001, DFIP-SR-002, and DFIP-SR-003. DFIP-SR-004 and DFIP-SR-005 were not covered by executed STP cases.

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

The executed test cases passed, with 25 of 33 STP cases completed and 8 cases not run. The security tests TC-SEC-01, TC-SEC-02 and TC-SEC-03 passed, while TC-SEC-04 and TC-SEC-05 remain not run. The UI acceptance test TC-UX-01 also remains not run.

One Minor defect remains Open: #61 — Admin cannot create users with an `@dfip.local` email. The execution log records that the issue was not reproduced or reclassified during this run.

Although all executed cases passed, the evidence is incomplete. This report does not establish full STP completion or release readiness. The remaining tests and open defect require review by the QA lead and team.
