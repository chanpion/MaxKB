# syntax=docker/dockerfile:1
# MaxKB FastAPI backend — production image.
#
# Multi-stage build: a `build` stage resolves and installs all dependencies with
# `uv` (the project uses `uv` rather than pip, see pyproject.toml `[tool.uv]`),
# then a slim `runtime` stage copies the virtualenv + application code.
#
# The same image serves both the API process (SERVICE_MODE=web) and the arq
# worker (SERVICE_MODE=worker); see docker-entrypoint.sh.

# ---------------------------------------------------------------------------
# Build stage
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS build

ENV DEBIAN_FRONTEND=noninteractive \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv (https://docs.astral.sh/uv/)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Install dependencies first (leverages Docker layer caching).
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project

# Copy the application source and finish the sync (project code is on PYTHONPATH).
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# ---------------------------------------------------------------------------
# Runtime stage
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    SERVICE_MODE=web \
    MAXKB_WEB_HOST=0.0.0.0 \
    MAXKB_WEB_PORT=8080

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 postgresql-client redis-tools curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bring in the virtualenv produced by the build stage (keep its bin on PATH).
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:${PATH}"

# Bring in uv so `uv run` works in the entrypoint without a full reinstall.
COPY --from=build /root/.local/bin/uv /usr/local/bin/uv

# Deployment helpers (init DDL, schema reference, entrypoint).
COPY init.sql schema.sql docker-entrypoint.sh ./

RUN chmod +x docker-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/app/docker-entrypoint.sh"]
