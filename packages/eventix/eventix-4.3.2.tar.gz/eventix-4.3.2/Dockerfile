FROM python:3.13-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    dnsutils \
    inetutils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Environment variables
ENV EVENTIX_API_PORT=8000 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Copy application code
COPY . /app/

# Install dependencies and the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --group server

# Expose port
EXPOSE $EVENTIX_API_PORT

# Health check
HEALTHCHECK \
    --interval=60s \
    --timeout=10s \
    --start-period=2s \
    --start-interval=1s \
    --retries=3 \
    CMD curl --fail http://localhost:$EVENTIX_API_PORT/healthz || exit 1

# Start supervisord
CMD ["uv", "run", "supervisord", "-c", "supervisord.conf"]
