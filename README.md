# Address Enrichment Pipeline

A production-minded full-stack application that turns messy address text into structured, usable location data.

This project demonstrates how to design and ship a real-world data pipeline, not just an API demo. It combines parsing, enrichment, geocoding, security controls, and a usable frontend experience in one coherent system.

## Why This Project Matters

Address quality issues create real operational cost: failed deliveries, broken analytics, and poor customer records. This system tackles that problem with a staged pipeline that favors reliability, traceability, and sensible fallback behavior.

Key outcomes:

- Converts raw address strings into normalized structured components.
- Preserves lineage across every processing stage.
- Adds confidence and cost telemetry for practical decision-making.
- Supports role-based access for write operations.
- Surfaces results in a workflow-friendly web interface.

## What It Includes

### End-to-end processing pipeline

1. Parse stage (stubbed libpostal-style normalization)
2. LLM gap-fill stage
3. Search fallback stage for missing fields
4. Geocode stage with nearby business context

### Backend

- FastAPI service with typed request/response contracts
- SQLAlchemy + Alembic for persistence and schema evolution
- PostgreSQL with pgvector support
- JWT authentication with refresh flow
- RBAC enforcement (`admin` required for write actions)
- Login rate limiting and audit logging with redaction

### Frontend

- React + TypeScript + Vite
- TanStack Query for server-state management
- Protected routes and role-aware UX
- Pipeline submission, ranked result list, and detail views

### Delivery and operations

- CI workflow for linting, tests, and build verification
- Dockerized local stack
- Azure deployment scaffolding for cloud rollout

## Architecture Snapshot

```mermaid
flowchart LR
    A[Raw Address Input] --> B[Parse Result]
    B --> C[Enrichment Result]
    C --> D[Geocode Result]
    D --> E[API and UI Detail Views]
```

Core data entities:

- `user`
- `raw_input`
- `parse_result`
- `enrichment_result`
- `geocode_result`
- `audit_event`

This structure keeps every stage inspectable and makes retries, debugging, and quality analysis straightforward.

## API Surface

### Health

- `GET /health`

### Authentication

- `POST /auth/register`
- `POST /auth/token`
- `POST /auth/refresh`
- `GET /auth/me`

### Parse and listing

- `POST /parse` (`admin`)
- `GET /parse/{parse_id}`
- `GET /parse/{parse_id}/summary`
- `GET /parses`
- `GET /inputs`

### Enrichment

- `POST /enrich` (`admin`)

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop

### 1) Start PostgreSQL

```powershell
docker compose up -d postgres
```

### 2) Start backend

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
..\.venv\Scripts\alembic.exe upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3) Start frontend

```powershell
cd frontend
npm install
npm run dev
```

## Configuration

Create `.env` from `.env.example`.

Common variables:

- `DATABASE_URL`
- `APP_ENV`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`
- `OPENAI_API_BASE_URL`
- `OPENAI_API_KEY`
- `SERPER_API_KEY`
- `EMBEDDINGS_PROVIDER`
- `EMBEDDINGS_MODEL`
- `EMBEDDINGS_DIMENSION`

## Testing

### Backend

```powershell
cd backend
..\.venv\Scripts\pytest.exe -q
```

### Frontend unit tests

```powershell
cd frontend
npm run test
```

### Frontend e2e tests

```powershell
cd frontend
npm run test:e2e
```

## What This Demonstrates (For Hiring Managers)

This repository is a practical example of full-stack engineering across product, platform, and reliability concerns:

- Designing a staged data pipeline with clear fallbacks
- Building secure APIs with auth, RBAC, and auditability
- Shipping an operator-friendly frontend on top of backend workflows
- Managing schema lifecycle with migrations and strong typing
- Integrating testing and CI/CD into day-to-day development
- Preparing code for deployment, not only local execution

## Tech Stack

- Python, FastAPI, SQLAlchemy, Alembic
- PostgreSQL, pgvector
- React, TypeScript, Vite, TanStack Query
- Pytest, Vitest, Playwright
- Docker, GitHub Actions, Azure deployment scaffolding

## License

Add your preferred license (for example, MIT or Apache-2.0) if this repository will be shared publicly.
# Address Enrichment Pipeline

Address Enrichment Pipeline is a full-stack application that converts raw address input into structured, reviewable records through a staged flow:

1. Parse (stubbed libpostal-style normalization)
2. LLM enrichment (gap fill)
3. Search fallback (when needed)
4. Geocode and nearby-business context

The project includes authentication, RBAC for write operations, audit logging, token/cost telemetry, embeddings support with pgvector, and CI/CD/deployment scaffolding.

## What It Does

- Accepts raw addresses and stores immutable input records.
- Produces parse results with confidence/completeness metadata.
- Runs enrichment and geocode steps as a pipeline with trace data.
- Persists each stage independently for auditability and retries.
- Exposes list/detail APIs for inputs and parses with filtering/pagination.
- Provides a React UI for login, submission, ranked results, and detail inspection.

## Architecture

### Backend

- Framework: FastAPI
- ORM/Migrations: SQLAlchemy + Alembic
- Database: PostgreSQL + pgvector
- Auth: JWT access/refresh tokens
- Authorization: role-based write access (`admin` required for create/enrich)
- Security controls:
  - rate limiting on login
  - CORS allowlists
  - audit events with address redaction for sensitive actions

### Frontend

- Framework: React + TypeScript + Vite
- Data layer: TanStack Query
- Routing: React Router
- Testing: Vitest + Playwright

### Data Flow

```mermaid
flowchart LR
    A[Raw Address Input] --> B[Parse Result]
    B --> C[Enrichment Result]
    C --> D[Geocode Result]
    D --> E[Detail and Summary Views]
```

## Repository Structure

```text
backend/
  app/
    api/routers/      # auth, parse, enrich routes
    core/             # settings, security, rate limiting
    db/               # base/session
    llm/              # embeddings and summary utilities
    models/           # SQLAlchemy models
    schemas/          # Pydantic contracts
    services/         # enrich/geocode/audit/cost helpers
  alembic/
  scripts/
  tests/
frontend/
  src/
    api/
    components/
    hooks/
    pages/
    types/
.github/workflows/    # CI + deploy workflow
```

## API Overview

### Health

- `GET /health`

### Authentication

- `POST /auth/register`
- `POST /auth/token`
- `POST /auth/refresh`
- `GET /auth/me`

### Parse and Input

- `POST /parse` (`admin`)
- `GET /parse/{parse_id}`
- `GET /parse/{parse_id}/summary`
- `GET /parses`
- `GET /inputs`

### Enrichment

- `POST /enrich` (`admin`)

Interactive API docs are available at `/docs` in development mode. Docs are disabled when `APP_ENV=production`.

## Data Model

The system stores each stage as a separate table:

- `user`
- `raw_input`
- `parse_result`
- `enrichment_result`
- `geocode_result`
- `audit_event`

This model supports lineage, retries, operational visibility, and post-run analysis.

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop

### 1) Start PostgreSQL

From repository root:

```powershell
docker compose up -d postgres
```

### 2) Backend setup

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
..\.venv\Scripts\alembic.exe upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3) Frontend setup

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173` by default.

## Configuration

Copy `.env.example` to `.env` and set values as needed.

Key variables:

- `DATABASE_URL`
- `APP_ENV`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`
- `OPENAI_API_BASE_URL`
- `OPENAI_API_KEY`
- `SERPER_API_KEY`
- `EMBEDDINGS_PROVIDER`
- `EMBEDDINGS_MODEL`
- `EMBEDDINGS_DIMENSION`

Notes:

- If LLM/search/geocode credentials are not configured, the pipeline uses fallback/stub behavior for those steps.
- Embeddings are configured for pgvector (`vector(384)` by default).

## Testing

### Backend

```powershell
cd backend
..\.venv\Scripts\pytest.exe -q
```

### Frontend unit tests

```powershell
cd frontend
npm run test
```

### Frontend e2e tests

```powershell
cd frontend
npm run test:e2e
```

## Docker Compose (Full Stack)

The repository includes compose services for `postgres`, `backend`, and `frontend`.

```powershell
docker compose up --build
```

## CI/CD and Deployment

- CI workflow in `.github/workflows/ci.yml` runs linting, tests, and image build checks.
- Azure deployment scaffolding is included via workflow and `deploy-azure.sh`.

## Security Notes

- Use a strong `JWT_SECRET_KEY` outside local development.
- Keep production docs disabled (`APP_ENV=production`).
- Restrict CORS origins to trusted hosts.
- Provide secrets through secure environment management (not committed files).

## License

Add your preferred license in this repository (for example, MIT or Apache-2.0) if you plan to distribute the project publicly.
