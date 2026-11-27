# syntax=docker/dockerfile:1

# --- Frontend build -------------------------------------------------------
FROM node:24-slim AS frontend
WORKDIR /src
COPY package.json package-lock.json tsconfig.base.json ./
COPY packages/core/package.json packages/core/
COPY frontend/package.json frontend/
RUN npm ci
COPY packages/core packages/core
COPY frontend frontend
RUN npm run build

# --- Python runtime -------------------------------------------------------
FROM python:3.13-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.9.30 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    FORWARDED_ALLOW_IPS=127.0.0.1

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/app app
COPY backend/alembic alembic
COPY backend/alembic.ini ./
COPY --from=frontend /src/frontend/dist static

RUN useradd --system --uid 10001 --no-create-home app
USER app

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips \"$FORWARDED_ALLOW_IPS\""]
