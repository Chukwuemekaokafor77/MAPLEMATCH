# MapleMatch — Project Guidelines

AI-Powered Affordable Housing Matching Platform for Canada. See `docs/VISION.md` for the full project spec and feature roadmap.

## Architecture

Turborepo monorepo with three packages:

| Package | Stack | Path |
|---------|-------|------|
| **web** | Next.js 16, React 19, TypeScript, Tailwind, shadcn/ui | `apps/web/` |
| **api** | Python 3.12, FastAPI (async), SQLModel | `apps/api/` |
| **mobile** | React Native (Expo) | `apps/mobile/` |

Key services: PostgreSQL 16 + PostGIS + pgvector, Redis (cache/queues), Clerk (auth).

Data flow: `User → Clerk Auth → Eligibility Engine → Matching Service → Listings API → Frontend`

All data must reside in Canadian cloud regions (AWS ca-central-1 or GCP northamerica-northeast1).

## Build and Test

```bash
# Install & run (from repo root)
npm install                    # Frontend + monorepo deps

# Backend (virtual environment — always use venv)
cd apps/api
python -m venv .venv
.venv/Scripts/activate         # Windows (.venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
cd ../..

turbo dev                      # Start all apps

# Frontend (apps/web/)
npm run dev                    # Vite dev server
npm run build                  # Production build (tsc + vite build)
npm run preview                # Preview production build

# Backend (apps/api/)
uvicorn app.main:app --reload  # FastAPI dev server
pytest                         # All tests
pytest --cov=app               # With coverage
ruff check --fix && ruff format # Lint + format

# Docker
docker compose up              # Full stack (Postgres, Redis, API, Web)
```

## Code Style

### TypeScript (frontend)
- Strict mode. No `any` unless unavoidable.
- Use `react-i18next` for all user-facing strings — never hardcode EN or FR text.
- State: Zustand for global, TanStack Query for server state.
- Components: shadcn/ui + Radix primitives. No custom component when shadcn has one.
- React Router for client-side routing.

### Python (backend)
- Type hints on all function signatures.
- Async endpoints (`async def`) by default.
- SQLModel for ORM; Alembic for migrations.
- Pydantic v2 for request/response schemas.
- Format and lint with **Ruff** (`ruff check --fix && ruff format`). No Black/isort/flake8 — Ruff replaces them all.

## Conventions

- **Bilingual from day 1**: Every user-facing string goes through i18n (`en.json` / `fr.json`). Never commit hardcoded display text.
- **PIPEDA compliance**: Minimize data collection. Require explicit consent. No analytics without opt-in.
- **Accessibility**: WCAG 2.2 AA minimum — ARIA labels, keyboard nav, colour contrast. Test with screen reader.
- **RBAC roles**: `applicant`, `admin`, `nonprofit`. Guard every API route and page.
- **Security**: OWASP Top 10 — parameterized queries, input sanitization, rate limiting, HTTPS only, encrypted document storage.
- **Ethical AI**: Matching engine must provide explainable results. Audit training data for bias.
- **Tests**: Target 90%+ coverage. Every new endpoint gets a test. Integration tests for the matching engine.
- **Performance & Scalability**: <2s page loads. Lazy load heavy components. Use edge caching where possible. Design APIs for pagination. Use connection pooling, async I/O, and background tasks (Redis queues) for heavy work. Index database queries. Plan for horizontal scaling from the start.
- **Documentation**: Keep README with architecture diagram. API docs via Swagger/OpenAPI. Maintain `.env.example`.
- **Canadian-first**: Use open gov datasets (CMHC). Support remote/low-bandwidth users.
- **Open-source**: MIT license for core matching engine.
- **Environment**: Use `.env.example` as the template. Never commit secrets.

## Key Files

```
apps/web/src/              # React app source
apps/web/src/components/   # React components
apps/web/src/i18n/         # EN/FR translation files
apps/web/index.html        # Vite entry HTML
apps/api/app/main.py       # FastAPI entrypoint
apps/api/app/models/       # SQLModel database models
apps/api/app/routers/      # API route modules
apps/api/app/services/     # Business logic (matching, eligibility, OCR)
docker-compose.yml         # Local dev stack
turbo.json                 # Turborepo pipeline config
```

## Development Workflow

Follow this phase order. See `docs/VISION.md` for full details.

| Phase | Focus |
|-------|-------|
| 0 | Project setup — monorepo, Next.js + FastAPI, Clerk auth, i18n, Tailwind, shadcn |
| 1 | Database & Auth — SQLModel schema, auth flows, role guards |
| 2 | Core Backend APIs — eligibility engine, listings CRUD, geospatial search, OCR pipeline |
| 3 | AI Matching Engine — vector embeddings, hybrid recommender, wait-time model, explainability |
| 4 | Frontend & Mobile — dashboard, wizard, map UI, React Native mobile |
| 5 | Integrations & Polish — CMHC sync, notifications, bilingual + a11y audit |
| 6 | Testing & Deploy — full test suite, security scan, Canadian-region deploy |
| 7 | Iteration — Phase 2 features |