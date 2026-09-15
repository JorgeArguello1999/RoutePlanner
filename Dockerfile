# Single-image RoutePlanner - SQLite by default, MySQL/PostgreSQL via DATABASE_URL
FROM python:3.13-slim

WORKDIR /app

# curl for HEALTHCHECK only (no mysql-client needed, drivers are Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=ghcr.io/astral-sh/uv:latest /uvx /bin/uvx

# Install Python dependencies first for better layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Copy application code
COPY . .

# Ensure entrypoint is executable and instance dir exists for SQLite
RUN chmod +x ./entrypoint.sh && mkdir -p /app/instance

EXPOSE 8003

ENV HOST=0.0.0.0
ENV PORT=8003
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
# Safe defaults (overridable via .env / -e)
ENV SECRET_KEY=dev-secret-key-change-in-production
ENV ENCRYPTION_KEY=0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=
ENV CONFIG_ACCESS_KEY=admin
ENV ADMIN_USERNAME=admin
ENV ADMIN_EMAIL=admin@routeplanner.local
ENV ADMIN_PASSWORD=Admin123!

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
