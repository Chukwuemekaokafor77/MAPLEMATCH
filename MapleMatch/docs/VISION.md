# MapleMatch — Project Vision & Roadmap

## Purpose

Eliminate the chaos of finding affordable housing in Canada by instantly matching low/moderate-income households (including newcomers, families fleeing violence, seniors, and Indigenous applicants) with available non-market units, rent-geared-to-income (RGI) options, subsidies, co-ops, and waitlists.

Goal: Reduce placement time from months to days, cut homelessness risk, and work seamlessly for urban, rural, and remote users.

## MVP Features

1. User onboarding (roles: Applicant, Admin, Non-profit)
2. Eligibility wizard (income, household size, priority groups, location)
3. AI smart matching engine (semantic + rule-based + predictive)
4. Real-time listings dashboard with filters, proximity search, virtual tours
5. Document upload + OCR verification (income proofs, ID)
6. Predictive wait-time estimator
7. Bilingual (EN/FR) UI with accessibility-first design
8. Secure messaging & notification system

## Phase 2 (Post-MVP)

- Integration with CMHC Open Data, provincial portals (NB Housing, etc.)
- Indigenous-language support
- Community resource map (shelters, legal aid)
- Admin analytics dashboard

## Tech Stack

### Frontend
- Vite + React 19 + TypeScript
- Tailwind CSS + shadcn/ui + Radix primitives
- React Native (Expo) for mobile
- react-i18next for bilingual i18n
- React Router for client-side routing
- TanStack Query + Zustand for state

### Backend
- Python 3.12 + FastAPI (async)
- PostgreSQL 16 + PostGIS (geospatial)
- Redis (caching, rate limiting, queues)
- pgvector for embeddings

### AI / ML
- scikit-learn + LightGBM/XGBoost (matching & wait-time prediction)
- LangChain + LlamaIndex (semantic search & document parsing)
- sentence-transformers / Cohere for embeddings
- Tesseract / Google Document AI for OCR

### Auth & Security
- Clerk (Canadian data residency)
- MFA, RBAC, JWT
- End-to-end encryption for documents

### Infrastructure
- Vercel (frontend) + Render or AWS/GCP Canadian regions (backend)
- GitHub Actions CI/CD
- Sentry + PostHog (privacy-first analytics)
- Docker + docker-compose for local dev

### Integrations
- CMHC Open Data API
- Google Maps / Mapbox
- Stripe (future premium features)
- Uploadcare or Cloudinary + OCR

## Development Phases

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| 0 | Project setup | Monorepo, Vite + React + FastAPI init, Clerk auth, i18n, Tailwind, shadcn |
| 1 | Database & Auth | SQLModel schema, auth flows, role guards |
| 2 | Core Backend APIs | Eligibility engine, listings CRUD, geospatial search, OCR pipeline |
| 3 | AI Matching Engine | Vector embeddings, hybrid recommender, wait-time model, explainability |
| 4 | Frontend & Mobile | Dashboard, wizard, map UI, React Native mobile |
| 5 | Integrations | CMHC sync, notifications, bilingual + accessibility audit |
| 6 | Testing & Deploy | Full test suite, security scan, production deploy (Canadian regions) |
| 7 | Iteration | Phase 2 features |
