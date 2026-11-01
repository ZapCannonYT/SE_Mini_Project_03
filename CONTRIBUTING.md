# Contributing

One issue, one branch, one PR. `main` is protected, so all changes go through a PR.

## Workflow
1. Move your card to **In Progress** on the board.
2. `git checkout main && git pull`
3. `git checkout -b feat/<short-name>`
   Allowed prefixes: `feat/`, `fix/`, `test/`, `docs/`, `chore/`, `ci/`, `refactor/`. Lower case, no spaces.
4. Make small commits (3-5 per story).
5. `git push -u origin feat/<short-name>`, then `gh pr create --base main --reviewer <your-reviewer>`.
6. Fill in the PR template and move the card to **In Review**.
7. After one approval and green checks, the repo owner merges with **Squash and merge**.

## Reviewers
Vishnu reviews Sahana, Sahana reviews Preksha, Preksha reviews Rahul, Rahul reviews Vishnu.

## Commit messages and PR titles
Use Conventional Commits, for example:
- `feat(api): add inventory update with validation`
- `fix(import): reject rows with future dates`
- `test(planning): cover zero-stock reorder case`
- `docs: update README`

Types: `feat`, `fix`, `test`, `docs`, `chore`, `ci`, `refactor`.

## The `conventions` check requires
- a Conventional Commit PR title and an allowed branch name
- `Closes #<issue number>` in the PR body
- Summary, Requirements covered and Test cases filled in
- every checklist item ticked (only tick what is true)

If it fails, fix the description; editing it re-runs the check.

## Do not commit
`.env`, `.venv/`, `node_modules/`, `__pycache__/`, database files (`*.db`), real passwords or large datasets.
Put new settings in `.env.example` with placeholder values.

## Before opening a PR
- `pytest` passes locally
- Requirement IDs (DFIP-F-xxx / NF / SR) and test case IDs (TC-xxx) are listed in the PR
- Docs updated if you changed behaviour or an API
- Commit as yourself, with an email verified on your GitHub account

Any change from the submitted SRS/SAD/STP goes into the deviations log in the sprint plan.
