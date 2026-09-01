# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# default-mysql-client para esperar a MySQL / healthchecks
# curl para healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=ghcr.io/astral-sh/uv:latest /uvx /bin/uvx

# Copy the project configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies
# --system instala en el python del sistema (container) para que entrypoint y gunicorn lo encuentren sin .venv
RUN uv sync --frozen --no-cache --system

# Copy the application code
COPY . .

# Asegurar permisos de ejecución para entrypoint
RUN chmod +x ./entrypoint.sh

# Expose the port the app runs on (requerido: 8003)
EXPOSE 8003

# Variables por defecto - pueden sobreescribirse en docker-compose / .env
ENV HOST=0.0.0.0
ENV PORT=8003
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
# Valores dev por defecto (en compose se sobreescriben con secrets)
ENV SECRET_KEY=dev-secret-key-change-in-production
ENV ENCRYPTION_KEY=0A1glB0r_8tPpo8k9eeWZW3TXvkvCPpw1ZgBmsV5D6s=
ENV CONFIG_ACCESS_KEY=admin
ENV ADMIN_USERNAME=admin
ENV ADMIN_EMAIL=admin@routeplanner.local
ENV ADMIN_PASSWORD=Admin123!

# Healthcheck interno
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${PORT}/ || exit 1

# Entrypoint robusto: espera DB, migra, crea tablas, seed admin y arranca gunicorn
ENTRYPOINT ["./entrypoint.sh"]
