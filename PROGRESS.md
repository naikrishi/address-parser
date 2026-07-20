## Session Log

- 2026-07-20: Completed Git workflow practice for repo initialization, first commit, remote setup, and feature branch -> PR -> merge cycle. Files touched: `.gitignore`, `PROGRESS.md`. Learned: the full Git loop is clearer when practiced on the real repo, and keeping `.gitignore` in place early avoids accidental local-environment commits. Next: return to Week 1 Day 5 database bootstrap work.
- 2026-07-20: Audited and aligned `PROGRESS.md` with `AP_Plan.md` tracking requirements. Files touched: `PROGRESS.md`. Learned: Day-by-day checklist and milestone-state formatting must be explicit so session handoffs are reliable. Next: start Day 5 database bootstrap (Postgres + first models + first migration).
- 2026-07-20: Implemented Day 4 API scaffold and verification. Files touched: `backend/main.py`, `backend/requirements.txt`, `PROGRESS.md`. Learned: local FastAPI setup works with corporate package proxy, and `/docs` plus `/health` are reachable as expected. Next: continue Week 1 contract work and define normalized schema/completeness rules.
- 2026-07-20: Started re-scoping the repo from the old intern-directory plan to the address enrichment pipeline. Files touched: `README.md`, `PROGRESS.md`. Learned: Week 1 should define the address contract, escalation rules, and fallback behavior before implementation. Next: rewrite or refine the Week 1 plan details for the address pipeline.
- 2026-07-20: Replaced the old intern-directory roadmap with an address-pipeline version of `PLAN.md`. Files touched: `PLAN.md`, `PROGRESS.md`. Learned: the same month-long structure can map cleanly onto parsing, enrichment, search, geocoding, and enterprise reliability concerns. Next: confirm the README and plan stay aligned on the project scope and Week 1 deliverables.
- 2026-07-20: Added the Week 1 data model to `README.md` for `raw_input`, `parse_result`, `enrichment_result`, `geocode_result`, and `user`, including relationship rules and an ER diagram. Files touched: `README.md`, `PROGRESS.md`. Learned: keeping each stage as its own table preserves provenance, retry history, and confidence/cost analysis. Next: define the normalized address JSON schema and completeness criteria.

## Current Focus

- Week 1 execution for the address enrichment pipeline.
- Day 4 complete; Git workflow practice completed; next implementation task is Day 5 database connection and schema bootstrap.

## Next Actions

1. Start Day 5: run Postgres in Docker for local development.
2. Create SQLAlchemy models for `raw_input` and `parse_result`.
3. Initialize Alembic and run the first migration.
4. Confirm the normalized address schema and completeness criteria against model fields.
5. Gain access to install postgres, wsl, nodejs

## Status at a Glance

- Week 1: 🟡 in progress
- Milestone 1 (Data Backbone): 🟡 on track
- Day 4 (API fundamentals): ✅ complete
- Day 5 (DB connection + schema): ⏳ next

## Day-by-Day Checklist (Week 1)

- [x] Day 1 — Requirements and scope in `README.md` (users, stories, out-of-scope, sketch prompts).
- [x] Day 2 — Environment baseline established and Python tooling validated.
- [x] Day 3 — Data model documented in `README.md` (`raw_input`, `parse_result`, `enrichment_result`, `geocode_result`, `user`).
- [x] Day 4 — `backend/` scaffolded, `GET /health` created, `/docs` and `/health` verified.
- [ ] Day 5 — Postgres in Docker + SQLAlchemy models (`raw_input`, `parse_result`) + first Alembic migration.
- [ ] Day 6 — First parsing endpoints with persistence (`POST /parse`, `GET /parse/{id}`, `GET /inputs`).
- [ ] Day 7 — Buffer/review + realistic seed data and reflection notes.

## What Exists So Far

| File | State | Notes |
|---|---|---|
| `README.md` | updated | Reframed project and added the Week 1 data model and relationships. |
| `AP_Plan.md` | updated/existing | Address-pipeline month plan and day-by-day source of truth. |
| `PLAN.md` | updated | Rewritten as an address-pipeline roadmap with the same month-long structure. |
| `PROGRESS.md` | initialized | Added the first session log and current focus. |
| `.gitignore` | created | Ignores local Python environment files, caches, and coverage artifacts. |
| `backend/main.py` | created | FastAPI app with `GET /health` endpoint. |
| `backend/requirements.txt` | created | Day 4 runtime dependencies (`fastapi`, `uvicorn`). |

## Key Decisions Made

- Week 1 should prioritize specification and validation boundaries before any implementation work.
- The monthly plan structure, tech stack, and professional workflow skills remain the same; only the app domain and daily tasks changed.
- The data model uses stage-separated tables (`raw_input` -> `parse_result` -> `enrichment_result` -> `geocode_result`) to preserve lineage and retries.
- Local Git practice should happen against the actual project repo so branching, remote sync, and merge flow are learned in the same environment as the codebase.
