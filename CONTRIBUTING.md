# Contributing

## Workflow
1. `git checkout main && git pull`
2. `git checkout -b <type>/<short-name>` — e.g. `feat/auth-rbac`, `fix/csv-dates`, `docs/v1.1`
3. Commit in small steps, then `git pull --rebase origin main` before pushing.
4. `git push -u origin <branch>` and open a PR. Fill in the template, including requirement IDs.
5. One teammate reviews; merge with **Squash and merge**. Delete the branch after merging.

Never push directly to `main`.

## Commit messages
Use `type(scope): summary`, for example:
- `feat(api): add inventory update with validation (F-006)`
- `fix(import): reject rows with future dates`
- `test(planning): cover zero-stock reorder case`
- `docs(sad): add ER diagram`

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.

## Do not commit
`.env`, `.venv/`, `node_modules/`, `__pycache__/`, database files (`*.db`), real passwords or large datasets.
Put new settings in `.env.example` with placeholder values.

## Before opening a PR
- `pytest` passes locally
- Requirement IDs (DFIP-F-xxx / NF / SR) and test case IDs (TC-xxx) are listed in the PR
- Docs updated if you changed behaviour or an API
