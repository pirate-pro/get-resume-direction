nothing here!
# China Job Aggregator (MVP)

FastAPI + PostgreSQL + SQLAlchemy 2.0 + Alembic + APScheduler based job aggregation skeleton.

## Monorepo Apps

- Backend API: `app/` (Python, `uv`)
- Frontend web: `apps/web` (Next.js, `npm`)

## Quick Start

1. Copy env:
   - `cp .env.example .env`
2. Install deps:
   - `uv sync`
3. Migrate DB:
   - `uv run alembic upgrade head`
4. Seed demo sources:
   - `uv run python scripts/seed_sources.py`
5. Start API:
   - `uv run uvicorn app.main:app --reload`

## Demo

- Trigger crawl:
  - `POST /api/v1/crawler/runs`
  - body: `{ "source_code": "demo_platform", "trigger_type": "manual" }`
- Search jobs:
  - `GET /api/v1/jobs?page=1&page_size=20`

## Frontend Quick Start

1. Install frontend deps:
   - `cd apps/web && npm i`
2. Configure API URL:
   - `cp .env.example .env.local`
   - set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
3. Start frontend:
   - `npm run dev`
