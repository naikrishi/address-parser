## Session Log

- 2026-08-03: Implemented Days 9 and 10 end-to-end and validated with 27 passing tests. Day 9: upgraded Postgres image to `pgvector/pgvector:pg16`, added `pgvector`, `sentence-transformers`, `tenacity`, `openai`, `pydantic-settings` to requirements; extended `config.py` to a full `Settings` class with embeddings, LLM, Serper, cost, and proxy vars; added `embedding vector(384)` column to `ParseResult`; created migration `a1b2c3d4e5f6` which enables the pgvector extension and adds embedding plus telemetry columns; implemented `app/llm/embeddings.py` with deterministic serializer, local sentence-transformers provider, company API placeholder, tenacity retry, and dimension validation; created idempotent backfill script at `backend/scripts/backfill_embeddings.py`. Day 10: added `confidence_label`, `prompt_tokens`, `completion_tokens`, `estimated_cost`, `llm_summary` to `EnrichmentResult`; added `prompt_tokens`, `completion_tokens`, `estimated_cost` to `GeocodeResult`; implemented `app/llm/summarize.py` with LLM-based confidence scoring and summary generation plus rule-based fallbacks; implemented `app/services/cost.py` (token-to-USD estimator); implemented Step 2 and Step 3 in `app/services/enrich.py`; implemented Step 4 in `app/services/geocode.py` with Serper fallback and regex business-address backfill; created `app/schemas/enrich.py`; implemented full `POST /enrich` orchestrator in `app/api/routers/enrich.py`; added `GET /parse/{id}/summary` to parse router; registered enrich router in `app/main.py`; added 19 new tests (embeddings + enrich endpoints) for 27 total. Applied migration, confirmed head at `a1b2c3d4e5f6`, all 27 tests passed. Files touched: `docker-compose.yml`, `backend/requirements.txt`, `.env.example`, `backend/app/core/config.py`, `backend/app/models/parse_result.py`, `backend/app/models/enrichment_result.py`, `backend/app/models/geocode_result.py`, `backend/alembic/versions/a1b2c3d4e5f6_day9_10_embeddings_and_telemetry.py`, `backend/app/llm/embeddings.py`, `backend/app/llm/summarize.py`, `backend/app/services/parse.py`, `backend/app/services/enrich.py`, `backend/app/services/geocode.py`, `backend/app/services/cost.py`, `backend/app/schemas/enrich.py`, `backend/app/api/routers/enrich.py`, `backend/app/api/routers/parse.py`, `backend/app/main.py`, `backend/scripts/backfill_embeddings.py`, `backend/tests/test_embeddings.py`, `backend/tests/test_enrich_endpoints.py`, `README.md`, `PROGRESS.md`. Learned: sentence-transformers downloads the model on first call (~90 MB); mock `_local_model` in tests to avoid download latency in CI. Next: begin Day 11/12 frontend work or proceed to Week 3 auth.

 Verified migration head is `5d6a6d3f9c12 (head)` and reran `pytest tests/test_parse_endpoints.py -q` with `8 passed`. Also added Day 9 embeddings env scaffolding to `.env.example` (`EMBEDDINGS_PROVIDER`, model/dimension, API URL/key placeholders, timeout/fallback toggle) so planning can move straight into implementation prerequisites. Files touched: `.env.example`, `PROGRESS.md`. Learned: the updated AP plan introduces concrete Day 9 provider/model requirements that need explicit env placeholders even before code changes. Next: begin Day 9 implementation planning with pgvector extension strategy, embedding column migration, provider fallback logic in `llm/embeddings.py`, and seed-data backfill workflow.

- 2026-07-23: Follow-up validation pass completed against a live Postgres instance. Confirmed `alembic upgrade head` applies cleanly and current revision is `5d6a6d3f9c12`. Ran `pytest tests/test_parse_endpoints.py -q` against the migrated database and fixed one query bug surfaced during the run: `max(UUID)` in PostgreSQL is invalid for latest-status aggregation. Replaced that logic with PostgreSQL-safe `DISTINCT ON` style selection ordered by `created_at`, then re-ran tests to green. Final state: `8 passed` in focused endpoint suite. Files touched: `backend/app/api/routers/parse.py`, `PROGRESS.md`. Learned: database-level validation is essential for aggregation logic because type/operator behavior can differ from assumptions made during pure code review. Next: optionally reduce warning noise by moving `datetime.utcnow` defaults to timezone-aware UTC and tracking upstream FastAPI/Python 3.14 deprecation warnings.

- 2026-07-23: Completed Week 2 Day 8 implementation for relationships and richer queries, then aligned repository scaffolding to the target file/folder structure in `AP_Plan.md`. Added `enrichment_result` and `geocode_result` ORM models, new Alembic migration `5d6a6d3f9c12`, richer parse/input query shapes, expanded endpoint tests, `backend/app/main.py` as the canonical FastAPI entrypoint with a compatibility shim in `backend/main.py`, backend service/LLM/router placeholders, frontend scaffold files, backend container/packaging scaffolds, and a placeholder GitHub Actions workflow. Files touched: `backend/app/models/enrichment_result.py`, `backend/app/models/geocode_result.py`, `backend/app/models/parse_result.py`, `backend/app/models/raw_input.py`, `backend/app/models/__init__.py`, `backend/alembic/env.py`, `backend/alembic/versions/5d6a6d3f9c12_add_enrichment_and_geocode_results.py`, `backend/app/schemas/parse.py`, `backend/app/schemas/__init__.py`, `backend/app/api/routers/parse.py`, `backend/tests/test_parse_endpoints.py`, `backend/app/main.py`, `backend/main.py`, `backend/app/core/security.py`, `backend/app/api/routers/auth.py`, `backend/app/api/routers/enrich.py`, `backend/app/api/routers/geocode.py`, `backend/app/services/__init__.py`, `backend/app/services/parse.py`, `backend/app/services/enrich.py`, `backend/app/services/geocode.py`, `backend/app/llm/__init__.py`, `backend/app/llm/embeddings.py`, `backend/app/llm/summarize.py`, `backend/Dockerfile`, `backend/pyproject.toml`, `.github/workflows/ci.yml`, `frontend/Dockerfile`, `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tailwind.config.js`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/index.ts`, `frontend/src/components/index.ts`, `frontend/src/pages/index.ts`, `frontend/src/hooks/index.ts`, `frontend/src/types/index.ts`, `README.md`, `PROGRESS.md`. Learned: the cleanest Day 8 shape is parse-centric detail plus separate parse-list and input-list query surfaces, and scaffolding the target repo layout early reduces later path churn. Next: finish trustworthy executable validation in the repo venv, then move to Day 7 seed/review work or begin real enrichment/geocode service extraction.

- 2026-07-22: Completed Week 1 Day 6 end-to-end implementation and verification for first parsing endpoints. Added API router/dependency scaffolding, Pydantic schemas/validation, and endpoints `POST /parse`, `GET /parse/{id}`, `GET /inputs` with persistence to `raw_input` and `parse_result`. Added endpoint integration tests and executed both automated and live verification (5 fake address inserts plus read-back/list checks). Files touched: `backend/main.py`, `backend/requirements.txt`, `backend/app/db/session.py`, `backend/app/schemas/__init__.py`, `backend/app/schemas/parse.py`, `backend/app/api/__init__.py`, `backend/app/api/deps.py`, `backend/app/api/routers/__init__.py`, `backend/app/api/routers/parse.py`, `backend/tests/test_parse_endpoints.py`, `README.md`, `PROGRESS.md`. Learned: a Windows-stable sync SQLAlchemy session path is the most reliable baseline for current environment while preserving Day 6 endpoint contracts and testability. Next: move to Day 7 buffer/review work by seeding realistic data and documenting reflections from Week 1.
- 2026-07-21: Added a repository `.gitattributes` with cross-platform line-ending defaults to prevent noisy LF/CRLF warnings and keep Python/config files normalized. Files touched: `.gitattributes`, `PROGRESS.md`. Learned: setting eol policy at repo level is the simplest way to keep Windows and non-Windows contributors in sync. Next: run `git add --renormalize .` and inspect `git status` before commit.
- 2026-07-21: Reviewed implementation against `AP_Plan.md` and `README.md` requirements for architecture, format, and Day 5 scope. Kept Day 5 implementation intact and applied correctness fixes: UUID ORM field annotations were updated from `str` to Python `UUID` types, an unused import was removed from Alembic env config, and README out-of-scope wording was aligned to Week 1 (not the full month) to match AP plan sequencing. Files touched: `backend/app/models/raw_input.py`, `backend/app/models/parse_result.py`, `backend/alembic/env.py`, `README.md`, `PROGRESS.md`. Learned: keeping documentation scope synchronized with the phased plan prevents false constraints when later milestones intentionally add auth, deployment, and observability. Next: begin Day 6 endpoint implementation using the now-stable DB model + migration baseline.
- 2026-07-21: Completed Week 1 Day 5 database bootstrap end-to-end. Started Docker Postgres, added SQLAlchemy + psycopg + Alembic dependencies, implemented ORM models for `raw_input` and `parse_result`, initialized Alembic, autogenerated first migration, and applied it to Postgres. Files touched: `backend/requirements.txt`, `backend/app/core/config.py`, `backend/app/db/base.py`, `backend/app/db/session.py`, `backend/app/models/raw_input.py`, `backend/app/models/parse_result.py`, `backend/app/models/__init__.py`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/d23a9abb64c2_create_raw_input_and_parse_result_tables.py`, `PROGRESS.md`. Learned: wiring Alembic `target_metadata` to a shared Declarative Base plus importing model modules is the key step for reliable autogeneration. Next: start Day 6 by adding `POST /parse`, `GET /parse/{id}`, and `GET /inputs` backed by DB sessions.
- 2026-07-20: Added safe pre-Day-5 scaffolding from `AP_Plan.md` Section 6 without implementing DB models/migrations yet. Files touched: `docker-compose.yml`, `.env.example`, `backend/app/__init__.py`, `backend/app/db/__init__.py`, `backend/app/models/__init__.py`, `backend/app/schemas/__init__.py`, `backend/tests/__init__.py`, `PROGRESS.md`. Learned: creating only Day-5-safe structure keeps momentum while avoiding premature Alembic/model churn. Next: implement SQLAlchemy models and Alembic initialization in one focused Day 5 change set.
- 2026-07-20: Completed Git workflow practice for repo initialization, first commit, remote setup, and feature branch -> PR -> merge cycle. Files touched: `.gitignore`, `PROGRESS.md`. Learned: the full Git loop is clearer when practiced on the real repo, and keeping `.gitignore` in place early avoids accidental local-environment commits. Next: return to Week 1 Day 5 database bootstrap work.
- 2026-07-20: Audited and aligned `PROGRESS.md` with `AP_Plan.md` tracking requirements. Files touched: `PROGRESS.md`. Learned: Day-by-day checklist and milestone-state formatting must be explicit so session handoffs are reliable. Next: start Day 5 database bootstrap (Postgres + first models + first migration).
- 2026-07-20: Implemented Day 4 API scaffold and verification. Files touched: `backend/main.py`, `backend/requirements.txt`, `PROGRESS.md`. Learned: local FastAPI setup works with corporate package proxy, and `/docs` plus `/health` are reachable as expected. Next: continue Week 1 contract work and define normalized schema/completeness rules.
- 2026-07-20: Started re-scoping the repo from the old intern-directory plan to the address enrichment pipeline. Files touched: `README.md`, `PROGRESS.md`. Learned: Week 1 should define the address contract, escalation rules, and fallback behavior before implementation. Next: rewrite or refine the Week 1 plan details for the address pipeline.
- 2026-07-20: Replaced the old intern-directory roadmap with an address-pipeline version of `AP_PLAN.md`. Files touched: `AP_PLAN.md`, `PROGRESS.md`. Learned: the same month-long structure can map cleanly onto parsing, enrichment, search, geocoding, and enterprise reliability concerns. Next: confirm the README and plan stay aligned on the project scope and Week 1 deliverables.
- 2026-07-20: Added the Week 1 data model to `README.md` for `raw_input`, `parse_result`, `enrichment_result`, `geocode_result`, and `user`, including relationship rules and an ER diagram. Files touched: `README.md`, `PROGRESS.md`. Learned: keeping each stage as its own table preserves provenance, retry history, and confidence/cost analysis. Next: define the normalized address JSON schema and completeness criteria.

## Current Focus

- Week 2 LLM pipeline complete (Days 9 and 10). All 27 tests passing.
- Next: Day 11 frontend scaffold or Week 3 auth (JWT, protected endpoints).

## Next Actions

1. Decide whether to proceed to Day 11 (frontend scaffold) or Week 3 (auth / JWT / protected endpoints) first.
2. When LLM credentials are available, set `OPENAI_API_BASE_URL`, `OPENAI_API_KEY`, and optionally `SERPER_API_KEY` in `.env` and smoke-test `POST /enrich` against a real address via Swagger.
3. Run `python -m scripts.backfill_embeddings --dry-run` to verify embedding backfill path before running live against all rows.
4. Optionally: switch to timezone-aware `datetime.now(timezone.utc)` across ORM defaults to clear deprecation warnings.

## Status at a Glance

- Week 1: 🟡 mostly complete, Day 7 buffer/review still open
- Week 2: 🟡 in progress
- Milestone 1 (Data Backbone): ✅ functionally achieved
- Milestone 2 (It's Alive on Screen): ⚪ not started, scaffold only
- Day 4 (API fundamentals): ✅ complete
- Day 5 (DB connection + schema): ✅ complete
- Day 6 (parse endpoints + persistence): ✅ complete
- Day 8 (relationships + richer queries): ✅ implementation and focused validation complete
- Day 9 (embeddings): ✅ complete — pgvector, embedding column, sentence-transformers, backfill script
- Day 10 (full enrichment pipeline): ✅ complete — 4-step pipeline, confidence, cost, summary endpoint

## Day-by-Day Checklist (Week 1)

- [x] Day 1 — Requirements and scope in `README.md` (users, stories, out-of-scope, sketch prompts).
- [x] Day 2 — Environment baseline established and Python tooling validated. Practice Git workflow.
- [x] Day 3 — Data model documented in `README.md` (`raw_input`, `parse_result`, `enrichment_result`, `geocode_result`, `user`).
- [x] Day 4 — `backend/` scaffolded, `GET /health` created, `/docs` and `/health` verified.
- [x] Day 5 — Postgres in Docker + SQLAlchemy models (`raw_input`, `parse_result`) + first Alembic migration. (Completed 2026-07-21 with migration `d23a9abb64c2` applied.)
- [x] Day 6 — First parsing endpoints with persistence (`POST /parse`, `GET /parse/{id}`, `GET /inputs`). (Completed 2026-07-22 with persistence, validation, tests, and live 5-address verification.)
- [ ] Day 7 — Buffer/review + realistic seed data and reflection notes.

## Day-by-Day Checklist (Week 2)

- [x] Day 8 — Relationships and richer queries. Added `enrichment_result` and `geocode_result`, joined parse detail reads, parse/input filtering, pagination, and test coverage. (Completed and revalidated on 2026-07-23 with migration head + focused tests green.)
- [x] Day 9 — LLM integration part 1 (embeddings): pgvector extension, embedding column, sentence-transformers provider, company API placeholder, backfill script. (Completed 2026-08-03; all 27 tests pass, migration at a1b2c3d4e5f6.)
- [x] Day 10 — LLM integration part 2 (full pipeline): POST /enrich with Steps 1-4, GET /parse/{id}/summary, confidence scoring, cost estimator, tenacity retry, Serper placeholder. (Completed 2026-08-03.)

## What Exists So Far

| File | State | Notes |
|---|---|---|
| `README.md` | updated | Reframed project and added the Week 1 data model and relationships. |
| `AP_Plan.md` | updated/existing | Address-pipeline month plan and day-by-day source of truth. |
| `PROGRESS.md` | initialized | Added the first session log and current focus. |
| `.gitignore` | created | Ignores local Python environment files, caches, and coverage artifacts. |
| `docker-compose.yml` | created | Local Postgres service scaffold for Day 5 development. |
| `.env.example` | created | Example app and database environment variables for local setup. |
| `.env.example` | updated | Added Day 9 embedding provider placeholders (model/dimension/API/fallback controls). |
| `backend/app/` | created | Package scaffolding with `db`, `models`, and `schemas` subpackages. |
| `backend/tests/` | created | Test package scaffold for backend tests. |
| `backend/main.py` | created | FastAPI app with `GET /health` endpoint. |
| `backend/requirements.txt` | updated | Added Day 5 dependencies (`SQLAlchemy`, `alembic`, `psycopg[binary]`). |
| `backend/app/core/config.py` | created | Central database URL resolution for app and migrations. |
| `backend/app/db/base.py` | created | Shared SQLAlchemy Declarative Base metadata. |
| `backend/app/db/session.py` | created | SQLAlchemy engine and session factory bootstrap. |
| `backend/app/models/raw_input.py` | created | ORM model for raw address submissions. |
| `backend/app/models/parse_result.py` | created | ORM model for parser outputs with FK to `raw_input`. |
| `backend/alembic.ini` | created | Alembic configuration file. |
| `backend/alembic/env.py` | updated | Wired to app metadata and `DATABASE_URL`. |
| `backend/alembic/versions/d23a9abb64c2_create_raw_input_and_parse_result_tables.py` | created | Initial migration for `raw_input` and `parse_result`. |
| `backend/app/models/raw_input.py` | updated | Corrected UUID column Python typing to `UUID` for type/schema alignment. |
| `backend/app/models/parse_result.py` | updated | Corrected UUID column Python typing to `UUID` for type/schema alignment. |
| `backend/alembic/env.py` | updated | Cleaned unused import during format/correctness review. |
| `README.md` | updated | Scoped out-of-scope section to Week 1 to match AP plan milestone sequencing. |
| `.gitattributes` | created | Enforces repo-wide line-ending policy (LF for code/config, CRLF for Windows scripts). |
| `backend/app/api/__init__.py` | created | API package scaffold for router/dependency organization. |
| `backend/app/api/deps.py` | created | Shared DB dependency (`get_db`) for endpoint handlers. |
| `backend/app/api/routers/__init__.py` | created | Router package scaffold. |
| `backend/app/api/routers/parse.py` | created | Day 6 endpoints: `POST /parse`, `GET /parse/{id}`, `GET /inputs`. |
| `backend/app/schemas/parse.py` | created | Day 6 request/response contracts with Pydantic validation. |
| `backend/app/schemas/__init__.py` | updated | Exports Day 6 parse schemas for package-level imports. |
| `backend/main.py` | updated | Compatibility shim that re-exports `app` from `backend/app/main.py`. |
| `backend/app/db/session.py` | updated | Uses sync SQLAlchemy session path for Windows-stable runtime behavior. |
| `backend/requirements.txt` | updated | Added Day 6 test/runtime support packages (`pytest`, `httpx`). |
| `backend/tests/test_parse_endpoints.py` | created | Integration tests for create/read/list and validation/not-found behavior. |
| `README.md` | updated | Added Day 6 endpoint cheat sheet with run and payload examples. |
| `backend/app/main.py` | created | Canonical FastAPI entrypoint matching the target file/folder structure. |
| `backend/app/models/enrichment_result.py` | created | ORM model for downstream enrichment attempts tied to `parse_result`. |
| `backend/app/models/geocode_result.py` | created | ORM model for downstream geocode attempts tied to `parse_result` and optional enrichment lineage. |
| `backend/alembic/versions/5d6a6d3f9c12_add_enrichment_and_geocode_results.py` | created | Adds `enrichment_result` and `geocode_result` tables plus indexes. |
| `backend/app/api/routers/parse.py` | updated | Day 8 query surface adds nested detail reads, `GET /parses`, and richer `GET /inputs` filters. |
| `backend/app/schemas/parse.py` | updated | Day 8 response/list schemas for downstream lineage and richer queries. |
| `backend/tests/test_parse_endpoints.py` | updated | Added lineage and query-filter integration coverage. |
| `backend/Dockerfile` | created | Backend container scaffold aligned with the plan's target structure. |
| `backend/pyproject.toml` | created | Backend packaging and pytest scaffold aligned with target structure. |
| `backend/app/core/security.py` | created | Placeholder auth utility module for later milestones. |
| `backend/app/api/routers/auth.py` | created | Placeholder auth router matching planned structure. |
| `backend/app/api/routers/enrich.py` | created | Placeholder enrich router matching planned structure. |
| `backend/app/api/routers/geocode.py` | created | Placeholder geocode router matching planned structure. |
| `backend/app/services/` | created | Placeholder service-layer package for future router extraction. |
| `backend/app/llm/` | created | Placeholder LLM integration package for later milestones. |
| `.github/workflows/ci.yml` | created | Placeholder CI workflow so repository layout matches the plan. |
| `frontend/` | created | Frontend scaffold matching the target Week 2 structure. |

## Key Decisions Made

- Week 1 should prioritize specification and validation boundaries before any implementation work.
- The monthly plan structure, tech stack, and professional workflow skills remain the same; only the app domain and daily tasks changed.
- The data model uses stage-separated tables (`raw_input` -> `parse_result` -> `enrichment_result` -> `geocode_result`) to preserve lineage and retries.
- Local Git practice should happen against the actual project repo so branching, remote sync, and merge flow are learned in the same environment as the codebase.
- For Day 5 prep, add only neutral scaffolding first (compose/env/package layout), then implement models + Alembic together so the first migration reflects real metadata.
- Keep Day 5 schema types PostgreSQL-native (`UUID`, `JSON`) so future migrations stay compatible with planned pgvector/Postgres-first architecture.
- Align ORM Python field types with DB-native types early (e.g., `UUID` instead of `str`) so later schema and API contracts remain consistent.
- README scope statements should be phase-specific (Week 1 vs full month) to stay compatible with AP plan milestones.
- For Day 6, endpoint behavior is raw-address-in with deterministic server-side parse stub output; full libpostal integration is deferred to later milestones.
- `GET /inputs` returns a paginated object (`items`, `total`, `limit`, `offset`) to align with expected Week 2 UI data-fetch patterns.
- Use sync SQLAlchemy sessions in the current Windows environment to avoid async psycopg event-loop compatibility issues during local runs.
- For Day 8, keep the detail route parse-centric (`GET /parse/{id}`) and use separate parse-list vs input-list query surfaces so list endpoints stay summary-oriented.
- Store `geocode_result.parse_result_id` in addition to optional `enrichment_result_id` to keep downstream presence filtering simple and avoid unnecessary deep joins.
- Match the AP plan's target folder structure with scaffold files now, while keeping later-milestone modules clearly marked as placeholders rather than implying implementation.
- Add Day 9 embeddings env placeholders before implementation so provider/model/dimension decisions are explicit and trackable in config.
