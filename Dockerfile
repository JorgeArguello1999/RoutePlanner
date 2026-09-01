# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# default-mysql-client to wait for MySQL / healthchecks
# curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=ghcr.io/astral-sh/uv:latest /uvx /bin/uvx

# Copy the project configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies (creates .venv at /app/.venv)
RUN uv sync --frozen --no-cache

# Ensure venv is on PATH so entrypoint.sh can find flask/gunicorn/python
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Copy the application code
COPY . .

# Ensure entrypoint is executable
RUN chmod +x ./entrypoint.sh

# Expose the port the app runs on (required: 8003)
EXPOSE 8003

# Default environment variables - can be overridden in docker-compose / .env
ENV HOST=0.0.0.0
ENV PORT=8003
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
# Default dev values (overridden with secrets in compose)
ENV SECRET_KEY=dev-secret-key-change-in-production
ENV ENCRYPTION_KEY=0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=
ENV CONFIG_ACCESS_KEY=admin
ENV ADMIN_USERNAME=admin
ENV ADMIN_EMAIL=admin@routeplanner.local
ENV ADMIN_PASSWORD=Admin123!

# Internal healthcheck - verifies app + DB + demo user via /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Robust entrypoint: waits for DB, migrates, creates tables, seeds admin and starts gunicorn
ENTRYPOINT ["./entrypoint.sh"]
