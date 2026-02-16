# Web Frontend (Next.js)

Independent frontend app in monorepo for Job Aggregation & Recommendation Platform.

## Stack

- Next.js (App Router) + React + TypeScript
- TailwindCSS
- TanStack Query
- react-hook-form + zod
- ESLint + Prettier
- Vitest + Testing Library (baseline)

## Run

1. Install dependencies:
   - `npm i`
2. Configure backend URL:
   - `cp .env.example .env.local`
   - set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
3. Start development server:
   - `npm run dev`

## Quality checks

- `npm run lint`
- `npm run typecheck`
- `npm run test`

## Notes

- Frontend expects backend APIs:
  - `GET /api/v1/jobs`
  - `GET /api/v1/jobs/{id}`
  - `GET /api/v1/stats/basic`
- For local browser calls to backend domain, enable backend CORS for the frontend origin (`http://localhost:3000`).
