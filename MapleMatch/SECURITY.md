# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in MapleMatch, please report it responsibly.

**Do NOT open a public issue.** Instead, email: **security@maplematch.ca**

We will acknowledge receipt within 48 hours and provide a timeline for a fix.

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | ✅        |

## Security Measures

### Authentication & Authorization
- Clerk JWT (RS256) with JWKS-based key rotation
- Role-based access control (applicant, admin, nonprofit)
- Route-level authorization guards

### Data Protection
- All data stored in Canadian cloud regions (AWS ca-central-1 / GCP northamerica-northeast1)
- PIPEDA-compliant data collection with explicit user consent
- Parameterized database queries (SQLAlchemy/SQLModel) preventing SQL injection
- Pydantic v2 input validation on all API endpoints

### Infrastructure
- HTTPS enforced with HSTS headers in production
- Security headers: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy
- CORS restricted to configured origins with specific methods/headers
- Docker containers run as non-root users
- Dependabot automated dependency updates
- CI pipeline includes `pip-audit`, `bandit`, and `npm audit`

### Development
- No secrets in source control — `.env` is gitignored
- `.env.example` provided as template
- Ruff for Python linting (security rules enabled)
- ESLint for TypeScript linting
