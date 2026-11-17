# Sprint 1 - Review and Retrospective

**Dates:** Fri 30 Oct - Tue 10 Nov 2026 (re-baselined on 17 Nov from the original plan of 30 Oct - 3 Nov; the last Sprint 1 story merged on Wed 11 Nov, in the backlog-clearing window 11-12 Nov)
**Scrum Master:** Vishnu P
**Goal:** Secure core platform: scaffold, login and RBAC, product and inventory API, forecasting and planning engine (unit tested), UI shell on mock data.

## Review

| Issue | Story | Owner | SP | Result |
|---|---|---|---|---|
| #13 | Project scaffold | Vishnu | 3 | Done (#43, 1 Nov) |
| #14 | Database schema and models | Vishnu | 5 | Done (#49, 3 Nov) |
| #15 | Product and inventory API | Vishnu | 5 | Done (#50, 3 Nov) |
| #16 | Login and logout with hashed passwords | Sahana | 5 | Done (#48, 3 Nov) |
| #17 | Role-based access control | Sahana | 3 | Done (#51, 5 Nov) |
| #18 | User and role administration | Sahana | 3 | Done (#53, 5 Nov) |
| #19 | SRS, SAD and STP v1.1 consistency update | Sahana | 2 | Done (#57, 9 Nov) |
| #20 | Sales data preprocessing | Preksha | 3 | Done (#46, 3 Nov) |
| #21 | Demand forecasting engine | Preksha | 5 | Done (#52, 5 Nov) |
| #22 | Reorder quantity and stockout/overstock risk | Preksha | 5 | Done (#47, 3 Nov) |
| #23 | Frontend shell, navigation and login page | Rahul | 5 | Done (#54, 9 Nov) |
| #24 | Product, inventory and sales data screens | Rahul | 5 | Done (#55, 11 Nov) |
| #25 | Dashboard with summary cards and alerts (mock data) | Rahul | 3 | Done (#56, 11 Nov) |

**Completed:** 14 of 14 issues, 52 of 52 SP (13 SP per member), but 8 days after the planned end date.

**Increment on `main`:**
- Backend: FastAPI with JWT login and hashed passwords, RBAC, user administration, product and inventory API; 114 pytest tests.
- Analytics: preprocessing, forecasting engine, and reorder and risk rules as unit-tested functions (not yet exposed through the API).
- Frontend: React + Vite app with login, navigation, products, inventory, sales and dashboard on mock data; 54 vitest tests.
- CI: `lint`, `test`, `frontend` and `conventions` required on every PR; green on every merge to `main`.

**Release tag:** `v0.1.0` (Sprint 1 increment; Rahul tags it as part of the close-out).
**Demo video:** 1-minute working-product video, link to be added once recorded.

### Why the sprint ran late

- The scaffold (#13) merged on 1 Nov and login (#16) on 3 Nov. Almost every other story needed one or both, so most work could only start near the end of the originally planned dates.
- Several PRs waited a day or more for review or merge (for example #54, opened 6 Nov, merged 9 Nov).
- Branches built on top of unmerged branches had to be rebased after each squash merge.

## Retrospective

Each member's bullets are taken from the "Sprint 1 stand-ups" issue (#44).

### Vishnu
- Went well: the schema (#14) and the product and inventory API (#15) shipped with tests from the start, and the shared error format made the API easy for the frontend to mock.
- To change: foundation stories (scaffold, login) must be merged on day 1, because everything else waits on them.
- To change: do not stack a branch on an unmerged PR; wait for the merge and branch from `main` (now rule 5 of the Sprint 2 guide).

### Sahana
- _(to be added from #44)_

### Preksha
- _(to be added from #44)_

### Rahul
- _(to be added from #44)_

## Actions for Sprint 2

- Reviewers turn PRs around within 2 hours; the repo owner merges as soon as checks are green and a review is in.
- No stacked branches: branch from the latest `main` only after the story you depend on has merged.
- Agree API shapes before building. The frontend's sales and dashboard contracts are in the Sprint 2 guide (section 6).
- Testers write their test cases while features are being built, so testing starts as soon as the code merges.
- Stand-ups move to a new "Sprint 2 stand-ups" issue run by Preksha (Scrum Master for Sprint 2).

## Carried over to Sprint 2

Nothing. Every Sprint 1 story is closed. The late finish moved the schedule: Sprint 1 is now 30 Oct - 10 Nov, backlog clearing 11-12 Nov and Sprint 2 13-17 Nov. The original plan was Sprint 1 30 Oct - 3 Nov and Sprint 2 4-8 Nov, later compressed to 11-12 Nov; the 17 Nov re-baseline is recorded in the deviations log.
