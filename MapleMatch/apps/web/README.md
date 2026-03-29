# MapleMatch — Frontend

Next.js App Router frontend for MapleMatch. See the [root README](../../README.md) for full project documentation.

## Stack

- Next.js App Router + React + TypeScript
- Tailwind CSS v4 + shadcn/ui
- Clerk (auth)
- TanStack React Query (data fetching)
- react-i18next (EN/FR bilingual)

## Dev

```bash
npm install
npm run dev       # http://localhost:3000
npm run build
npm run lint
```

## Environment

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_API_URL=http://localhost:8000
```
