# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# libpq-dev is often needed for psycopg2 (PostgreSQL adapter), though we might be using binary wheels.
# curl is useful for healthchecks or installing tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy the project configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies
# We use --system to install into the system python environment since we are in a container
RUN uv sync --frozen --no-cache

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Define environment variable
ENV HOST=0.0.0.0
ENV PORT=5000

# Run the command to start the application
# Using uv run to ensure we use the environment created by uv (though --system might make it global)
# If we used --system in uv sync, we can just run python app.py or flask run
# Providing CMD to run the app directly
CMD ["uv", "run", "app.py"]
