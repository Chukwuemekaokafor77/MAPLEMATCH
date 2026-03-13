# MapleMatch

AI-Powered Affordable Housing Matching Platform for Canada.

## Status

**Branch**: `fix/security-updates` | **Last updated**: March 2026

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000 · Swagger UI: http://localhost:8000/docs
- **Database**: Local PostgreSQL (Docker) — 74 listings across all 13 provinces/territories
- **Authentication**: Clerk

## Quick Start

```bash
# 1. Start infrastructure (PostgreSQL + Redis)
docker run -d --name maplematch-postgres -p 5432:5432 \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=maplematch \
  postgis/postgis:16-3.4

docker run -d --name maplematch-redis -p 6379:6379 redis:7-alpine

# 2. Install frontend deps
npm install

# 3. Install backend deps
cd apps/api
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt

# 4. Run database migrations
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/maplematch" \
  python -m alembic upgrade head

# 5. Seed listings (74 listings, all 13 provinces/territories)
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/maplematch" \
  python scripts/seed_listings.py
cd ../..

# 6. Start the API (separate terminal)
cd apps/api
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/maplematch" \
REDIS_URL="redis://localhost:6379/0" \
CLERK_SECRET_KEY="<your-key>" \
JWKS_URL="https://<your-clerk-domain>/.well-known/jwks.json" \
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 7. Start the frontend (separate terminal)
npm run dev
```

## Features

| Feature | Status |
|---|---|
| User authentication (Clerk JWT) | Done |
| Eligibility wizard (4-step income/household profile) | Done |
| Housing listings with filters (province, city, rent, bedrooms, RGI, accessible) | Done |
| AI matching engine (rules + semantic + ML scoring) | Done |
| Wait-time prediction | Done |
| Document upload & OCR review | Done |
| Bilingual EN/FR interface | Done |
| WCAG-accessible UI (skip link, ARIA, screen reader) | Done |
| Real housing data pipeline | Done |
| Email notifications (SMTP) | Done |
| Admin sync/seed endpoints | Done |

## Real Data Pipeline

MapleMatch serves real Canadian affordable housing data without requiring any paid API credentials.

**Sources (tried in order on every sync):**

1. **Toronto Open Data CKAN** — Affordable Rental Housing Register (no auth)
2. **Canada Open Government Portal CKAN** — CMHC datasets (no auth)
3. **Built-in curated seed** — 74 listings across all 13 provinces/territories (always available)

**Seed coverage:**

| Province/Territory | Listings |
|---|---|
| Ontario (ON) | 18 |
| British Columbia (BC) | 10 |
| Alberta (AB) | 9 |
| Québec (QC) | 7 |
| Manitoba (MB) | 5 |
| New Brunswick (NB) | 4 |
| Newfoundland & Labrador (NL) | 4 |
| Nova Scotia (NS) | 4 |
| Saskatchewan (SK) | 4 |
| Prince Edward Island (PE) | 3 |
| Northwest Territories (NT) | 2 |
| Nunavut (NU) | 2 |
| Yukon (YT) | 2 |

**Re-seeding:**

```bash
# Via CLI script (no auth required)
cd apps/api
python scripts/seed_listings.py

# Filter to one province
python scripts/seed_listings.py --province BC

# Via API (admin role required)
POST /cmhc/seed
POST /cmhc/sync
```

## Architecture

```
apps/
  web/          Next.js 16 · React 19 · TypeScript · Tailwind v4 · shadcn/ui
  api/          Python 3.12 · FastAPI · SQLModel · asyncpg · httpx

Infrastructure:
  PostgreSQL 16 + PostGIS   (spatial queries, listings store)
  Redis 7                   (session cache, rate limiting)
  Clerk                     (JWT auth, Canadian data residency)
```

```mermaid
graph TB
    User --> Clerk[Clerk Auth]
    Clerk --> Web[Next.js Frontend]
    Clerk --> API[FastAPI Backend]
    Web --> API
    API --> OpenData[Toronto / Canada Open Data CKAN]
    API --> Seed[Built-in seed dataset]
    API --> DB[(PostgreSQL + PostGIS)]
    API --> Cache[(Redis)]
```

## Testing

```bash
# Backend
cd apps/api
pytest
pytest --cov=app                 # Coverage (90%+ enforced)
ruff check --fix && ruff format  # Lint + format

# Frontend
cd apps/web
npm test                         # Vitest + React Testing Library (51 tests)
npm run lint
npm run build
```

## Environment Variables

**`apps/api/.env`**
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/maplematch
REDIS_URL=redis://localhost:6379/0
CLERK_SECRET_KEY=sk_test_...
JWKS_URL=https://<clerk-domain>/.well-known/jwks.json
CORS_ORIGINS=["http://localhost:3000"]
DEBUG=true
```

**`apps/web/.env.local`**
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Optional — if you obtain CMHC API credentials:
```
CMHC_API_KEY=your-key
CMHC_API_URL=https://api.cmhc-schl.gc.ca
```

## Production Deployment

```bash
# Canadian cloud regions (data residency)
#   AWS: ca-central-1 (Montréal)
#   GCP: northamerica-northeast1 (Montréal)

docker compose -f docker-compose.prod.yml up -d
```

## CI/CD

GitHub Actions on every PR and push to `main`:
- Backend: Ruff lint → pytest (90%+ coverage) → pip-audit + bandit security scan
- Frontend: ESLint → Vitest → Next.js build
- Docker compose build check
- Dependabot for automated dependency updates

## Docs

- [Project Vision & Roadmap](docs/VISION.md)
- [Security Policy](SECURITY.md)
- API Reference: http://localhost:8000/docs (Swagger UI)

## License

MIT
