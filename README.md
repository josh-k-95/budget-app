# budget-app

A budgeting app for casual users: simple by default, grows with you. Self-hosted with Docker.
"budget-app" is a working name; the displayed name comes from `APP_NAME`.

Status: pre-release (0.1.0 in progress). See [docs/PLAN.md](docs/PLAN.md) for the roadmap.

## Quick start (Docker)

Requirements: Docker with Compose v2.

```bash
cp .env.example .env   # then set POSTGRES_PASSWORD (and DATABASE_URL to match) and PUBLIC_URL
docker compose up -d --build
```

Open http://localhost:8000. Health check: `GET /api/health`.

The app listens on one port and never terminates TLS. Put it behind HTTPS (Tailscale Serve,
Caddy, or any reverse proxy) and set `PUBLIC_URL` and `FORWARDED_ALLOW_IPS` accordingly.
Migrations run automatically when the app container starts.

## Development

Requirements: Node 24 (`.nvmrc`), [uv](https://docs.astral.sh/uv/), Docker.

```bash
npm install
cd backend && uv sync && cd ..
docker compose up -d db
cd backend && uv run alembic upgrade head && uv run uvicorn app.main:app --reload
npm run dev   # in another terminal: http://localhost:5173
```

Tests need a throwaway Postgres: `docker compose --profile test up -d db-test`.
All commands (tests, lint, migrations) are listed in [CLAUDE.md](CLAUDE.md#commands).

## Layout

| Path | What |
|---|---|
| `backend/` | FastAPI app, Alembic migrations, pytest tests |
| `frontend/` | React + TypeScript + Vite + Tailwind |
| `packages/core/` | Shared, pure TypeScript calculations |
| `deploy/` | Compose profiles (Tailscale; added in a follow-up) |
| `docs/` | Plan and setup guides |
