# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Install dependencies first for better layer caching. The forecasting extra
# (prophet/pandas/numpy/...) is heavy and off by default; build with
# `--build-arg INSTALL_FORECAST=true` and run with FORECASTS_ENABLED=1.
ARG INSTALL_FORECAST=false
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$INSTALL_FORECAST" = "true" ]; then \
        uv sync --frozen --no-dev --extra forecast; \
    else \
        uv sync --frozen --no-dev; \
    fi

# Application code.
COPY . .

# Dokploy maps this port; override with PORT if needed.
EXPOSE 8000

CMD ["sh", "-c", "gunicorn server:app -k gthread --threads 4 --bind 0.0.0.0:${PORT:-8000}"]
