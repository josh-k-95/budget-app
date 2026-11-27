# CLAUDE.md

Budgeting app for casual users: simple by default, grows with you through optional modules.
Self-hosted (Docker) until 1.0.0; 1.0.0 = public web + Android (Play Store) release.

Full roadmap and decisions: `docs/PLAN.md`. Read it before planning any feature.

## Current scope: 0.1.0 (Foundation)

Build ONLY what 0.1.0 lists below. Do not build later-version features, even partially.
New ideas or "would be nice" items go in `IDEAS.md`, not in code.

0.1.0 includes:
- Auth: register, login, logout. Multiple users. Login rate limiting. `ALLOW_SIGNUP` toggle.
  Password reset via server CLI command (no email).
- Transactions: add, edit, delete. List filtered by month.
  Fields: amount, type (income | expense), category, descriptor (free text), date, note (optional).
- Categories: user-created, typed income or expense.
- Mobile-friendly UI (375px and 1280px).
- Docker Compose deploy + Tailscale profile. Optional: minimal installable PWA (manifest only, no offline).
- Groundwork (see Architecture rules): budgets with members, default "Main" account, UUIDs,
  soft deletes, settings table with feature flags.

## Stack

| Layer | Choice |
|---|---|
| Frontend | React, TypeScript (strict), Vite, Tailwind CSS, React Router |
| Shared logic | `packages/core` — pure TypeScript functions, no I/O |
| Backend | Python, FastAPI, Uvicorn, SQLAlchemy 2.x, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Auth | Own implementation: `pwdlib` (Argon2) + DB-stored sessions + httpOnly cookie |
| Tests | pytest (backend), Vitest (frontend, core) |
| Lint/format | Ruff (Python), ESLint + Prettier (TS) |
| CI | GitHub Actions: lint + tests on every PR |
| Deploy | Docker Compose: one app container + Postgres |

Package managers: npm workspaces for `frontend/` + `packages/core/`. Python deps: propose `uv` + `pyproject.toml` in the scaffold plan and wait for approval.

## Repo layout

```
backend/        FastAPI app, Alembic migrations, tests
frontend/       React app
packages/core/  shared TS calculations (budget status, totals, etc.)
deploy/         compose profiles (tailscale), configs
docs/           PLAN.md, setup guides
docker-compose.yml
.env.example
CHANGELOG.md
IDEAS.md
CLAUDE.md
```

## Commands

Fill this section in once the repo is scaffolded (run, test, lint, migrate, build, reset-password). Keep it accurate.

## Architecture rules (non-negotiable)

**Data ownership**
- Data belongs to a **budget**, not a user. `budgets` + `budget_members (budget_id, user_id, role)`.
- On register, create a personal budget, the user as `owner`, and a default account "Main".
- Every domain table has `budget_id`. Every query is scoped to budgets the current user is a member of.
  Never trust a `budget_id` from the client without checking membership.
- Transactions have `account_id` (only "Main" is used in 0.1.0; no accounts UI yet).

**Records**
- UUID primary keys. Create endpoints accept an optional client-supplied UUID; if it already exists for that budget, return the existing record (idempotent).
- Every table: `created_at`, `updated_at`, `deleted_at`. Deletes are soft (set `deleted_at`). Queries exclude soft-deleted rows by default.
- Money: integer minor units (cents) in DB and API. Never floats. Single currency. `amount` is positive; `type` gives direction.
- Transaction `date` is a date (no time).

**Logic placement**
- Calculations (totals, budget status, etc.) go in `packages/core` as pure, tested functions.
- Backend stores, validates, authorizes. It does not own business calculations beyond what validation needs.

**Schema**
- Every schema change is an Alembic migration that preserves existing data. Never edit an applied migration.
- `user_settings` table with a JSON `feature_flags` field (unused in 0.1.0, must exist).

**HTTP / deploy**
- App listens on one port. FastAPI serves `/api/*` and the built frontend (SPA fallback to `index.html`).
- The app never terminates TLS. Trust proxy headers (`--proxy-headers`, `--forwarded-allow-ips` from env).
- `PUBLIC_URL` env var is the canonical external URL.
- `GET /api/health` returns DB connectivity status (used by Docker healthcheck).
- Login refused over plain HTTP unless host is localhost or `ALLOW_INSECURE_HTTP=true`.

## Auth details

- Hash passwords with `pwdlib` Argon2. Minimum password length 8 (configurable).
- Session token: 32 random bytes, sent to client in cookie; store only its SHA-256 hash in `sessions`.
- Cookie: `HttpOnly`, `Secure` (except localhost dev), `SameSite=Lax`, path `/`. Expiry 30 days, sliding.
- Logout deletes the session row.
- State-changing requests: verify `Origin` header matches `PUBLIC_URL` (CSRF defense).
- Rate limit login attempts per IP and per username (in-DB or in-memory; document the choice).
- `ALLOW_SIGNUP=false` blocks registration except when zero users exist (first user can always register).
- Password reset: CLI command run inside the backend container.
- Never log passwords, tokens, or cookie values.

## API conventions

- Prefix `/api`. JSON only. Resource routes: `/api/transactions`, `/api/categories`, `/api/auth/...`.
- Partial updates use PATCH and only change fields that were sent (`model_dump(exclude_unset=True)`).
- Errors: proper status codes; body `{ "detail": "..." }`.
- Pydantic schemas separate for Create / Update / Response.

## Frontend conventions

- API calls in `frontend/src/api/<resource>.ts`, one file per resource. Components never call `fetch` directly.
- Pages in `src/pages/`, reusable UI in `src/components/`.
- Tailwind mobile-first: base styles = phone; `md:`/`lg:` for larger. Sidebar on desktop, bottom nav or menu on mobile.
- Transaction list: table on desktop, cards on mobile. Amount inputs use `inputmode="decimal"`; convert to cents before sending.
- Accessibility: labelled inputs, keyboard usable, visible focus, sufficient contrast.
- Format numbers and dates with the browser locale (`Intl`).
- App name is not final ("budget-app" is a working name). Never hard-code the name in UI text, page titles,
  the PWA manifest, emails, or API responses. Read it from one config value: `APP_NAME` env var on the backend,
  exposed to the frontend via a single constant/config endpoint. Default: "Budget App".

## Testing

- Backend: test every endpoint, including auth-required behavior and cross-budget access (user A must never read/write user B's data).
- Core: unit-test every function in `packages/core`.
- Tests run against a real Postgres (compose test service or container), not SQLite.

## Workflow

- Branches: `feature/<name>` off `dev`; PR into `dev`; `dev` → `main` only for releases.
- Never commit to `main` or `dev` directly. Do not commit or push unless asked.
- For any non-trivial task: present a short plan first and wait for approval before writing code.
- Keep changes scoped to the task. No drive-by refactors.

## Definition of done (every task)

1. Tests and lint pass.
2. UI works at 375px and 1280px wide; no browser console errors.
3. Basic accessibility checks pass.
4. `git diff --stat` shows only intended files.
5. Reply ends with: one-line summary of what changed + suggested commit message.

## Stop and ask before

- Adding or upgrading any dependency.
- Any schema change or new migration.
- Deleting or renaming files.
- Anything touching auth, sessions, cookies, permissions, or security headers.
- Changing Docker, CI, or deploy config.
- Committing, pushing, or touching branches.
- Anything that conflicts with this file or `docs/PLAN.md`.

## Out of scope for 0.1.0 (do not build)

Budgets, dashboard, recurring, bills, multiple accounts UI, savings, CSV import, planning mode,
modules/tutorials, offline sync, envelopes, charts, sharing UI, search, Android, Caddy profile,
backups, email features.

## Keeping this file current

When a decision becomes permanent, update this file (ask first). At each release, update "Current scope" to the next version from `docs/PLAN.md`.
