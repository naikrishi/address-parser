# Address Enrichment Pipeline

A production-minded full-stack application that turns messy address text into structured, usable location data.

This project demonstrates how to design and ship a real-world data pipeline. It combines parsing, enrichment, geocoding, security controls, and a usable frontend experience in one system.

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

### Local-first pipeline configuration

For local-only runtime, set these in `.env` and leave remote keys empty:

```env
USE_LOCAL_MODELS_ONLY=true
LLM_LOCAL_PROVIDER=ollama
LLM_LOCAL_BASE_URL=http://127.0.0.1:11434
LLM_LOCAL_MODEL=qwen2.5:7b

GEOCODER_PROVIDER=nominatim
GEOCODER_BASE_URL=http://127.0.0.1:8080
```

Notes:

- If `USE_LOCAL_MODELS_ONLY=true` and a local LLM is not configured, enrichment steps return an error status instead of using remote providers.
- If local geocoder is not configured in local-only mode, geocode step falls back to `stub` provider.

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

## What This Demonstrates

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
