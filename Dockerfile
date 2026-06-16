# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Install dependencies first for better layer caching. The forecasting extra
# (prophet/pandas/numpy/...) is intentionally omitted; enable it by adding
# `--extra forecast` here and setting FORECASTS_ENABLED=1 at runtime.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Application code.
COPY . .

# Dokploy maps this port; override with PORT if needed.
EXPOSE 8000

CMD ["sh", "-c", "gunicorn server:app -k gthread --threads 4 --bind 0.0.0.0:${PORT:-8000}"]
