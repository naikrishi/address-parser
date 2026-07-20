# PLAN.md — One-Month End-to-End Software Development Learning Journey

> **Project:** "Address Enrichment Pipeline" — an internal tool that takes a raw address string and progressively enriches it into structured data using libpostal, LLM extraction, search-grounded fallback, and geocoding plus nearby-business backfill.
>
> **Format:** Learn by *examples* and *milestones*. Every week ends in something that runs
> and can be demoed. Every day = a concept + a hands-on task + a "why it matters" note.
>
> **Status:** This is a PLAN only. Nothing here has been executed. Switch to **code mode**
> to build it step by step.

---

## 0. ⚠️ MANDATORY: Keep `PROGRESS.md` Up To Date (read this first)

> This rule applies to **every AI assistant / session** working on this project. It is not
> optional. `PROGRESS.md` is the memory that survives between sessions — if it drifts out
> of sync with reality, the next session starts blind.

**At the START of every session:**
1. Read `PROGRESS.md` **before** doing anything else — specifically the *Current Focus*
   and *Next Actions* sections. That is your context for where things stand.
2. Read the relevant day/week in this `PLAN.md` for the task detail.

**At the END of every session (or after any meaningful change), you MUST update `PROGRESS.md`:**
1. **Session Log** — add a new dated entry on top (Did / Files touched / Learned / Next).
2. **Current Focus** — update the week, milestone, and "working on right now" line.
3. **Next Actions** — rewrite so the top item is the exact next thing to do.
4. **Day-by-Day Checklist** — tick `[ ]` → `[x]` for anything completed, with a one-line note.
5. **Status at a Glance** — update the week/milestone status emoji.
6. **What Exists So Far** — add/adjust rows for any files or components created or changed.
7. **Key Decisions Made** — log any meaningful decision (stack, library, pattern, tradeoff).

**Rules of thumb:**
- Never end a session that produced changes without updating `PROGRESS.md`.
- If you create a file, it goes in the "What Exists So Far" table.
- If you make a choice someone might question later, it goes in "Key Decisions Made".
- Keep entries terse and factual — this is a map, not an essay.
- If reality and `PROGRESS.md` disagree, fix `PROGRESS.md` immediately; it must always
  reflect the true current state of the repo.

---

## 1. Goal

By the end of one month you will have:

1. Built and deployed a **full-stack web application** from empty folder to live URL.
2. Practiced every layer of end-to-end development — the 7 skills you listed **plus** the
   9 missing ones a professional workflow requires (see §3).
3. Produced a real, useful internal tool: an address enrichment pipeline that parses raw
   addresses, fills gaps with LLMs, uses web search when needed, geocodes results, and
   backfills missing fields from nearby-business data.
4. Understood *why* each layer exists and how the layers connect — not just copied code.

**Definition of "done" for the month:** A user can open a deployed URL or API docs,
submit a raw address like "3400 W Plano Pkwy Plano TX", get a structured response from
libpostal when possible, fall back to LLM extraction and search-grounded enrichment when
needed, and finally receive coordinates plus nearby businesses with any remaining address
gaps backfilled — all running in the cloud, behind authentication, with tests and
monitoring in place.

---

## 2. Your Original 7 Skills — Mapped to This Plan

| # | Your skill | Where it's covered |
|---|-----------|--------------------|
| 1 | API understanding and setup | Week 1 (Days 4–7), reinforced all month |
| 2 | Database connection, access, writing, management | Week 1 (Days 5–7) + Week 2 (Day 8) |
| 3 | Access, tokens, authentication | Week 3 (Days 15–17) |
| 4 | Front-end and UI development | Week 2 (Days 11–14) |
| 5 | Cloud management and deployment | Week 4 (Days 22–25) |
| 6 | Security | Week 3 (Days 15–19) + threaded throughout |
| 7 | Performance optimization | Week 4 (Days 26–28) |

---

## 3. The 9 Skills You Were Missing (now added)

A truly *end-to-end* workflow needs more than the 7 above. I've completed your list:

| # | Added skill | Why it's essential | Where |
|---|------------|--------------------|-------|
| 8 | **Requirements & architecture design** | You can't build what you haven't specified. Diagrams and data models prevent expensive rework. | Week 1, Days 1–3 |
| 9 | **Version control & Git workflow** | Every professional change flows through Git: branches, commits, pull requests, code review. | Week 1, Day 2 (then daily) |
| 10 | **Data modeling / schema design** | Distinct from "connecting" to a DB — deciding *what* tables/relations exist is a skill of its own. | Week 1, Day 5 |
| 11 | **LLM integration (embeddings, semantic search, RAG)** | Your company builds language models — this is your differentiator, not an afterthought. | Week 2, Days 9–10 + Week 3 refinement |
| 12 | **Testing (unit / integration / e2e)** | Untested code is broken code you haven't caught yet. Enables safe change. | Week 2, Day 14 + Week 3, Day 20 |
| 13 | **Containerization (Docker)** | The bridge from "works on my machine" to "works in the cloud." | Week 4, Day 21 |
| 14 | **CI/CD pipelines** | Automate testing + deployment so shipping is safe and repeatable. | Week 4, Day 22 |
| 15 | **Observability (logging, monitoring, tracing)** | You can't fix what you can't see. Know when prod breaks *before* users tell you. | Week 4, Day 25 |
| 16 | **Data privacy / PII handling** | You store real address data and business lookup results. Legal + ethical requirement. | Week 3, Day 19 |

---

## 4. Recommended Tech Stack (and the reasoning)

| Layer | Choice | Why this, for *learning* |
|-------|--------|--------------------------|
| Language (backend) | **Python 3.12+** | Same ecosystem as LLM tooling; you'll reuse skills at work. |
| Backend framework | **FastAPI** | Modern async standard; **auto-generates interactive API docs** (Swagger) — perfect for *understanding* APIs (skill #1). |
| Database | **PostgreSQL** | Industry-standard relational DB; rock-solid; huge learning transfer. |
| Vector search | **pgvector** (Postgres extension) | Do semantic search *inside* the same DB — one fewer system to learn while still teaching embeddings/RAG. |
| ORM + migrations | **SQLAlchemy 2.0 (async) + Alembic** | Teaches both raw data modeling and safe schema evolution. |
| Frontend | **React + TypeScript + Vite** | The dominant UI stack in 2026; TypeScript teaches you type-safety habits. |
| UI styling | **Tailwind CSS** | Learn styling fundamentals fast without fighting CSS files. |
| Data fetching | **TanStack Query (React Query)** | Teaches client-side caching, loading/error states properly. |
| Auth | **JWT (access + refresh tokens) via OAuth2 password flow** | The canonical token-based auth pattern; directly teaches skill #3. |
| LLM / embeddings | **Your company's model API** (fallback: `sentence-transformers` local) | Real-world integration; local fallback keeps you unblocked and costs nothing. |
| Containers | **Docker + Docker Compose** | Standard local-to-cloud bridge. |
| CI/CD | **GitHub Actions** | Free, ubiquitous, great docs. |
| Deployment | **Railway or Render** (beginner-friendly) → optionally **AWS/Azure** later | Get to a live URL fast; graduate to a hyperscaler once concepts click. |
| Testing | **pytest** (backend), **Vitest + React Testing Library** (frontend), **Playwright** (e2e) | Covers all three test levels. |

> **Guiding principle:** *Build the boring version first, then add the smart version.*
> Get plain parsing working before adding embeddings. Get local working before cloud. Every
> milestone must run before you move on.

---

## 5. High-Level Architecture

```
                    ┌─────────────────────────────────────────┐
   Browser  ─────►  │  React + TypeScript SPA (Vite, Tailwind) │
   (ops / eng)      │  - Raw address input / results          │
                    │  - Pipeline trace / enrichment timeline  │
                    │  - Login screen / diagnostics dashboard  │
                    └───────────────────┬─────────────────────┘
                                        │  HTTPS + JWT (Bearer token)
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │  FastAPI backend (async)                 │
                    │  - /auth      (login, refresh, me)       │
                    │  - /parse     (libpostal baseline)       │
                    │  - /enrich    (LLM extraction + search)  │
                    │  - /geocode   (coords + nearby places)   │
                    │  - /compare   (Step 4 benchmark utility)  │
                    │  Layers: routers → services → models     │
                    └──────────┬────────────────────┬─────────┘
                               │                    │
                               ▼                    ▼
              ┌────────────────────────┐   ┌────────────────────┐
              │ PostgreSQL + pgvector  │   │  LLM / Embeddings   │
              │ - raw_inputs, parses    │   │  API (company model │
              │ - enriched_addresses    │   │  or local model)    │
              │ - embeddings, events    │   └────────────────────┘
              └────────────────────────┘
```

**Request flow example (address enrichment):**
1. User submits a raw address → React calls `POST /enrich`.
2. FastAPI runs libpostal to parse the string into structured pieces.
3. If the parse is incomplete, FastAPI calls an LLM to fill gaps from the raw input and parse.
4. If still incomplete, it escalates to a search-enabled LLM.
5. FastAPI geocodes the address, fetches nearby businesses, and backfills missing fields from the first nearby business address when needed.

---

## 6. Target File / Folder Structure

```
swe_learning/
├── PLAN.md                      # this file — the full month plan
├── PROGRESS.md                  # living progress tracker (update every session)
├── README.md                    # project overview + how to run
├── docker-compose.yml           # postgres + backend + frontend for local dev
├── .env.example                 # documented env vars (never commit real .env)
├── .github/
│   └── workflows/
│       └── ci.yml               # lint + test + build on every push
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml           # deps (fastapi, sqlalchemy, alembic, pgvector...)
│   ├── alembic/                 # database migrations
│   ├── app/
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── core/
│   │   │   ├── config.py        # settings from env (Pydantic BaseSettings)
│   │   │   └── security.py      # JWT create/verify, password hashing
│   │   ├── api/
│   │   │   ├── deps.py          # shared dependencies (get_db, current_user)
│   │   │   └── routers/
│   │   │       ├── auth.py
│   │   │       ├── parse.py
│   │   │       ├── enrich.py
│   │   │       └── geocode.py
│   │   ├── models/              # SQLAlchemy ORM models (tables)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # business logic (parse, enrichment, geocode)
│   │   ├── db/
│   │   │   └── session.py       # async engine + session factory
│   │   └── llm/
│   │       ├── embeddings.py    # embed text -> vector
│   │       └── summarize.py     # generate enrichment summaries / confidence
│   └── tests/                   # pytest unit + integration tests
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/                 # typed API client functions
        ├── components/          # reusable UI (Card, SearchBox, Nav)
        ├── pages/               # PipelinePage, DetailPage, LoginPage, Dashboard
        ├── hooks/               # useAuth, usePipeline (React Query)
        └── types/               # shared TypeScript types
```

---

## 7. The Four Milestones (the backbone of the month)

| Week | Milestone | You can demo… |
|------|-----------|---------------|
| **1** | **"The Data Backbone"** | A running API with `POST /parse` and a structured address response backed by a real Postgres DB, tested via auto-generated Swagger docs. |
| **2** | **"It's Alive on Screen"** | A React UI that submits raw addresses, shows pipeline steps, and surfaces semantic/LLM-based enrichment results. |
| **3** | **"Locked Down & Trustworthy"** | Login required, JWT-protected endpoints, role-based access, PII handled correctly, tested. |
| **4** | **"Shipped & Watched"** | The whole app containerized, auto-deployed via CI/CD to a public URL, with monitoring, logging, and performance tuning. |

---

## 8. Day-by-Day Guide

> Assume ~2–4 focused hours per weekday. Weekends are buffer/catch-up (marked). Adjust to
> your pace — the *milestones* matter more than the calendar.

### WEEK 1 — Foundations & The Data Backbone
**Milestone: a running, tested API backed by a real database.**

- **Day 1 — Requirements & scope (skill #8).**
  - *Concept:* user stories, MVP scoping, non-goals.
  - *Task:* Write `README.md` with: who the users are (ops, engineers, admins), 5–8 user stories
    ("As an ops user, I want to paste a raw address and get structured fields back…"), and an explicit
    out-of-scope list. Sketch the 3 core screens on paper.
  - *Why:* Every later decision traces back to a requirement. Prevents rework.

- **Day 2 — Environment + Git workflow (skill #9).**
  - *Concept:* Git branches, commits, `.gitignore`, pull requests, semantic commit messages.
  - *Task:* Install Python 3.12, Node 20+, Docker, PostgreSQL client. `git init`, create
    a GitHub repo, make your first commit, practice a feature branch → PR → merge cycle.
  - *Why:* This is the muscle memory of daily professional work.

- **Day 3 — Architecture & data model design (skill #8, #10).**
  - *Concept:* entities, relationships, ER diagrams; the request lifecycle.
  - *Task:* Draw the data model: `raw_input`, `parse_result`, `enrichment_result`, `geocode_result`, `user`, and how they relate. Write it up in the README.
  - *Why:* A good schema makes everything downstream easy; a bad one haunts you forever.

- **Day 4 — API fundamentals + FastAPI hello world (skill #1).**
  - *Concept:* HTTP methods, status codes, REST resources, JSON, what an "endpoint" is.
  - *Task:* Scaffold `backend/`, create `main.py` with a `GET /health` endpoint. Run it,
    open the **auto-generated Swagger docs** at `/docs`, call the endpoint from the browser.
  - *Why:* The interactive docs make abstract "API" concepts concrete and clickable.

- **Day 5 — Database connection + schema (skills #2, #10).**
  - *Concept:* relational DBs, tables, primary/foreign keys, ORMs, migrations.
  - *Task:* Run Postgres in Docker. Define SQLAlchemy models for `raw_input` and `parse_result`.
    Set up Alembic and run your first migration to create the tables.
  - *Why:* This is "database connection, access, management" made real.

- **Day 6 — First real parsing endpoints (skills #1, #2).**
  - *Concept:* create/read/update/delete; Pydantic request/response schemas; validation.
  - *Task:* Build `POST /parse`, `GET /parse/{id}`, `GET /inputs`, and a minimal persistence flow.
    Insert 5 fake addresses via Swagger; read them back.
  - *Why:* Parsing is the backbone of the pipeline; nail the pattern once and reuse it everywhere.

- **Day 7 — Weekend buffer / review.** Seed realistic sample data (10–15 fake addresses with
  partial parses, international formats, and malformed inputs). Write a short reflection on what clicked and what didn't.

**✅ Milestone 1 check:** You can start the API, open `/docs`, and submit addresses that persist in Postgres across restarts.

---

### WEEK 2 — Front-End, UI & The LLM Feature
**Milestone: a visible app with working address enrichment.**

- **Day 8 — Relationships & richer queries (skills #2, #10).**
  - *Task:* Add `enrichment_result` and `geocode_result` models with proper joins so a parse record can return all downstream steps in one call. Add pagination & filtering.
  - *Why:* Real data is relational; learn to query across tables efficiently.

- **Day 9 — LLM integration part 1: embeddings (skill #11).**
  - *Concept:* what an embedding is, vector similarity, why it helps with fuzzy address matching.
  - *Task:* Add pgvector extension + an `embedding` column. Write `llm/embeddings.py` to turn a raw address + parse into a vector (company API, or local `sentence-transformers` fallback). Backfill embeddings for your seed data.
  - *Why:* This is your company's domain — the feature that makes the app special.

- **Day 10 — LLM integration part 2: semantic search + summaries (skill #11).**
  - *Concept:* nearest-neighbor search, RAG basics, prompt design.
  - *Task:* Build `POST /enrich` (embed query → similarity + extraction → ranked candidates) and `GET /parse/{id}/summary` (LLM-generated summary of a parse and enrichment path). Test in Swagger.
  - *Why:* Turns a static parser into an intelligent, queryable enrichment system.

- **Day 11 — Frontend setup + first screen (skill #4).**
  - *Concept:* SPA, components, JSX/TSX, Vite dev server, Tailwind.
  - *Task:* Scaffold `frontend/` with Vite + React + TS + Tailwind. Build a static `PipelinePage` with hard-coded cards to learn the component model.
  - *Why:* Get comfortable with the rendering model before wiring in data.

- **Day 12 — Connecting frontend to backend (skills #1, #4).**
  - *Concept:* fetch/HTTP from the browser, CORS, TanStack Query, loading/error states.
  - *Task:* Create a typed API client; use React Query to load real parse records from `GET /inputs`. Handle loading spinners and error messages.
  - *Why:* This is the moment the two halves become one application.

- **Day 13 — Detail page + enrichment UI (skill #4).**
  - *Task:* Build `DetailPage` (raw input, libpostal parse, LLM extraction, search step, geocode results, nearby businesses) and a `SearchBox` that calls `POST /enrich` and renders ranked results.
  - *Why:* Delivers the core user experience from your Day 1 user stories.

- **Day 14 — Testing intro (skill #12) + weekend buffer.**
  - *Concept:* unit vs integration vs e2e; the test pyramid.
  - *Task:* Write pytest tests for the parsing service + a couple of API integration tests.
    Add one Vitest component test on the frontend.
  - *Why:* Now that things work, lock the behavior in so future changes don't break it.

**✅ Milestone 2 check:** In a browser you can submit addresses, inspect the parse, and run enrichment that returns ranked results and geocode output.

---

### WEEK 3 — Auth, Security, Privacy & Trust
**Milestone: the app is locked down, role-aware, and privacy-conscious.**

- **Day 15 — Auth concepts + user model (skills #3, #6).**
  - *Concept:* authentication vs authorization; password hashing (bcrypt/argon2); sessions vs tokens.
  - *Task:* Add a `user` table; implement secure registration with hashed passwords.
  - *Why:* Foundation for everything access-related.

- **Day 16 — JWT login + refresh tokens (skill #3).**
  - *Concept:* OAuth2 password flow, access vs refresh tokens, token claims (`exp`, `sub`).
  - *Task:* Build `POST /auth/token` (login) and `POST /auth/refresh`. Return short-lived access + longer refresh tokens.
  - *Why:* This is the canonical token-based auth pattern used across the industry.

- **Day 17 — Protecting endpoints + login UI (skills #3, #4).**
  - *Task:* Add a `current_user` dependency to guard `/parse`, `/enrich`, `/geocode`, `/compare`.
    Build the React `LoginPage`, store the token, attach it to every request, add logout.
  - *Why:* Ties the auth backend to a real user-facing flow.

- **Day 18 — Roles & access control (skills #3, #6).**
  - *Concept:* role-based access control (RBAC), object-ownership checks (BOLA).
  - *Task:* Add roles (`ops` = read + diagnostics, `admin` = full CRUD). Gate write endpoints to admins; hide admin UI from ops.
  - *Why:* Real orgs need different permissions for different people.

- **Day 19 — Security hardening + PII/privacy (skills #6, #16).**
  - *Concept:* OWASP basics, input validation, secrets management, CORS, rate limiting; what counts as PII and how to protect it.
  - *Task:* Move all secrets to env vars (never in code), lock down CORS to your frontend origin, add rate limiting on `/auth/token`, add an audit log for which user processed which address, document what personal data you store and why. Run `pip-audit`.
  - *Why:* You are storing real address data and geocoding results — this is a legal and ethical obligation, not a nice-to-have.

- **Day 20 — Integration testing for auth (skill #12).**
  - *Task:* Write tests for the negative paths: expired token, wrong role, no token, malformed token. Add a Playwright e2e test for the login → enrich flow.
  - *Why:* Auth bugs are security incidents — the failure cases matter most.

- **Day 21 (weekend) — Containerize (skill #13).**
  - *Concept:* images, containers, Dockerfiles, docker-compose.
  - *Task:* Write Dockerfiles for backend + frontend and a `docker-compose.yml` that runs Postgres + backend + frontend together with one command.
  - *Why:* This is the bridge to the cloud, and it makes onboarding trivial.

**✅ Milestone 3 check:** Nobody can reach the data without logging in; ops and admins see different things; secrets aren't in the code; auth failure cases are tested; the whole stack starts with `docker compose up`.

---

### WEEK 4 — Deploy, Observe & Optimize
**Milestone: live on the internet, monitored, fast.**

- **Day 22 — CI/CD pipeline (skill #14).**
  - *Concept:* continuous integration/deployment, GitHub Actions, pipeline stages.
  - *Task:* Write `.github/workflows/ci.yml` to lint + run tests + build Docker images on every push. Make a failing test block the merge.
  - *Why:* Automated safety net — shipping becomes routine instead of scary.

- **Day 23 — Cloud fundamentals + first deploy (skill #5).**
  - *Concept:* managed hosting, environment config, managed Postgres, build vs runtime.
  - *Task:* Deploy backend + a managed Postgres to Railway/Render. Get the API live at a public URL with `/docs` reachable (then gate docs for prod).
  - *Why:* "Works in the cloud" is a different skill from "works locally" — env config, networking, secrets all change.

- **Day 24 — Deploy frontend + wire it up (skills #5, #4).**
  - *Task:* Deploy the React build; point it at the live API; fix the inevitable CORS and env-var issues. Confirm the full flow works on the public URL.
  - *Why:* End-to-end in production is the real integration test.

- **Day 25 — Observability (skill #15).**
  - *Concept:* structured logging, metrics, health checks, error tracking, tracing.
  - *Task:* Add structured logging to the backend, a `/health` check the platform pings, and error tracking (e.g. Sentry free tier). Add basic request-latency logging.
  - *Why:* You can't operate what you can't see. Know about breakage before users do.

- **Day 26 — Performance: measure first (skill #7).**
  - *Concept:* profiling, the N+1 query problem, latency percentiles (p50/p95/p99).
  - *Task:* Load-test `/enrich` and `/parse`. Find the slow spots (likely network calls and un-indexed lookups). Measure before changing anything.
  - *Why:* Optimizing without measuring is guessing. Establish a baseline.

- **Day 27 — Performance: fix it (skill #7).**
  - *Concept:* DB indexes (incl. an HNSW index for pgvector), query optimization, caching, frontend bundle size.
  - *Task:* Add DB indexes + an HNSW vector index, fix N+1 queries with eager loading, add response caching for hot endpoints, lazy-load frontend routes. Re-measure vs baseline.
  - *Why:* This is skill #7 made concrete — turn measurements into real speedups.

- **Day 28 — Polish, docs & retrospective.**
  - *Task:* Update the README with architecture diagram, setup steps, and screenshots. Write a 1-page retrospective: what each of the 16 skills taught you, what was hardest, what you'd do differently. Tag a `v1.0` release.
  - *Why:* Documentation and reflection are what turn "I did it once" into "I can do it again."

**✅ Milestone 4 check:** A public URL where a user can submit a raw address, run enrichment, and see monitored, tested, containerized, auto-deployed code — and you can explain every layer.

---

## 9. Skill → Milestone Coverage Matrix

| Skill | W1 | W2 | W3 | W4 |
|-------|----|----|----|----|
| 1. APIs | ●● | ● | | |
| 2. Database | ●● | ● | | |
| 3. Auth & tokens | | | ●● | |
| 4. Frontend/UI | | ●● | ● | ● |
| 5. Cloud & deploy | | | | ●● |
| 6. Security | | | ●● | ● |
| 7. Performance | | | | ●● |
| 8. Requirements/architecture | ●● | | | |
| 9. Git workflow | ●● | ○ | ○ | ○ |
| 10. Data modeling | ●● | ● | | |
| 11. LLM / semantic search | | ●● | ○ | |
| 12. Testing | | ● | ● | ○ |
| 13. Docker | | | ● | ● |
| 14. CI/CD | | | | ●● |
| 15. Observability | | | | ●● |
| 16. Privacy / PII | | | ●● | |

(● = primary focus, ○ = reinforced/practiced)

---

## 10. Learning Tips

- **Type the code by hand** the first time; don't just paste. The friction is the learning.
- **Keep a daily log** of one thing that confused you and how you resolved it.
- **Commit small and often** with clear messages — your Git history becomes a study guide.
- **Build the boring version before the smart version** (plain parsing before semantic enrichment).
- **When stuck >30 min**, write down the exact error and what you expected — then search.
- **Every milestone must run** before you move on. A working small thing beats a broken big thing.

---

## 11. Open Questions for You (let's refine before coding)

1. **Pace:** Is ~2–4 hrs/weekday realistic, or should I stretch this to 6 weeks with lighter days?
2. **Language comfort:** Are you comfortable in Python and JavaScript/TypeScript, or should
   I add "language primer" mini-tasks in Week 1?
3. **LLM access:** Do you already have access to your company's model/embedding API, or
   should the plan default to the free local `sentence-transformers` path?
4. **Cloud provider:** Beginner-friendly (Railway/Render) as planned, or do you specifically
   need to learn AWS or Azure because that's what your company uses?
5. **Real vs. fake data:** Confirm we'll use *fake* seed data during learning (recommended
   for privacy) rather than real address data until the app is properly secured.
6. **Depth vs. breadth:** Do you want to go deeper on fewer topics (e.g. really master
   auth + LLM) or keep the broad end-to-end sweep as planned?

---

*Reminder: this document is a plan only — no code has been written or executed. Tell me how
you'd like to adjust it, and when you're happy, switch to **code mode** to start building
Week 1.*