# MapleMatch

AI-Powered Affordable Housing Matching Platform for Canada.

**Live:** https://web-eight-gamma-54.vercel.app &nbsp;|&nbsp; **API:** https://maplematch-api.onrender.com/docs

---

## What It Does

MapleMatch connects Canadians with affordable housing, subsidies, co-ops, and waitlists across all 13 provinces and territories. Applicants complete a short eligibility profile and get instantly matched with listings ranked by income, household size, priority group, and predicted wait time — powered by a three-layer AI scoring engine.

---

## Features

| Feature | Status |
|---|---|
| Clerk JWT authentication with auto-provisioning | ✅ |
| Eligibility wizard — income, household, location, consent | ✅ |
| Listings with real-time filters (province, city, rent, RGI, accessibility) | ✅ |
| Listing detail page with eligibility check + wait time estimate | ✅ |
| AI matching engine — rules + semantic + ML scoring | ✅ |
| Accept / decline matches with status tracking | ✅ |
| Document upload + admin review workflow (proto-KYC) | ✅ |
| Real-time notification bell | ✅ |
| Fully bilingual EN/FR interface | ✅ |
| WCAG-accessible UI (skip links, ARIA, screen reader support) | ✅ |
| Admin dashboard — pending docs, CMHC sync, sync history | ✅ |
| Rate limiting (120 req/min) | ✅ |
| Daily automated data sync via GitHub Actions | ✅ |

---

## Data Pipeline

MapleMatch pulls real Canadian affordable housing data from 6 free open-data sources — no paid API credentials required.

**Sources (polled on every sync):**

1. **Toronto Open Data CKAN** — Affordable Rental Housing Register
2. **Canada Open Government Portal CKAN** — CMHC datasets
3. **Ontario Data Catalogue CKAN** — provincial affordable housing
4. **BC Data Catalogue CKAN** — BC Housing registry
5. **Montreal Open Data CKAN** — social/affordable housing
6. **Alberta Open Data CKAN** — provincial housing programs
7. **Built-in curated seed** — 74 listings across all 13 provinces/territories (always available as fallback)

**Built-in seed coverage:**

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

Sync runs automatically every day at 06:00 UTC via GitHub Actions. Admins can also trigger a manual sync from the Admin Dashboard.

---

## Architecture

```
apps/
  web/    Next.js App Router · React · TypeScript · Tailwind · shadcn/ui
  api/    Python · FastAPI · SQLModel · asyncpg · Alembic

Infrastructure:
  Neon          Serverless PostgreSQL (Canadian data residency)
  Render        FastAPI backend (free tier, auto-deploy on push)
  Vercel        Next.js frontend (auto-deploy on push)
  Clerk         JWT auth + identity management
  GitHub Actions  Daily data sync cron (06:00 UTC)
```

```mermaid
graph TB
    User --> Clerk[Clerk Auth]
    Clerk --> Web[Next.js — Vercel]
    Web --> API[FastAPI — Render]
    API --> CKAN[6x CKAN Open Data Sources]
    API --> Seed[Built-in seed dataset]
    API --> DB[(Neon PostgreSQL)]
    GH[GitHub Actions cron] --> API
```

---

## Local Development

```bash
# 1. Start infrastructure
docker run -d --name maplematch-postgres -p 5432:5432 \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=maplematch \
  postgres:16

docker run -d --name maplematch-redis -p 6379:6379 redis:7-alpine

# 2. Backend setup
cd apps/api
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv/Scripts/activate         # Windows
pip install -r requirements.txt
python -m alembic upgrade head

# 3. Start API (port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Frontend setup (separate terminal)
cd apps/web
npm install
npm run dev                      # port 3000
```

---

## Environment Variables

**`apps/api/.env`**
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/maplematch
REDIS_URL=redis://localhost:6379/0
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
JWKS_URL=https://<clerk-domain>/.well-known/jwks.json
CORS_ORIGINS=["http://localhost:3000"]
SYNC_SECRET=<random-hex-secret-for-scheduled-sync>
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

---

## Production Deployment

| Service | Platform | Notes |
|---|---|---|
| Frontend | Vercel | Auto-deploys on push to `fix/security-updates` |
| Backend | Render | Auto-deploys on push; runs `alembic upgrade head` on build |
| Database | Neon | Serverless Postgres, Canadian region |

**Render environment variables required:**
`DATABASE_URL`, `CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `JWKS_URL`, `CORS_ORIGINS`, `SYNC_SECRET`

**GitHub Actions secret required:**
`SYNC_SECRET` — must match the value set on Render

---

## Admin Setup

After first sign-in, promote a user to admin via Neon SQL Editor:

```sql
UPDATE users SET role = 'admin' WHERE clerk_id = 'user_xxxxx';
```

The Admin tab appears in the nav automatically for admin-role users.

---

## API Reference

Swagger UI available at `/docs` on any running instance:
- Local: http://localhost:8000/docs
- Production: https://maplematch-api.onrender.com/docs

---

## License

MIT
