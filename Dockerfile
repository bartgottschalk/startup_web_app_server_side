# syntax=docker/dockerfile:1
# Multi-stage Dockerfile for StartupWebApp Backend
# Stages: base (shared) -> development (tests) -> production (deployment)

#############################################
# Base Stage: Common dependencies
#############################################
FROM python:3.12-slim as base

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies needed for psycopg2 and production
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

#############################################
# Development Stage: Includes testing tools
#############################################
FROM base as development

# Install Firefox ESR and geckodriver for Selenium tests
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver for Selenium
RUN GECKODRIVER_VERSION=0.33.0 && \
    wget -q https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz && \
    tar -xzf geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    rm geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz

# Copy project files
COPY StartupWebApp/ /app/

# Create directory for SQLite database (for local development)
RUN mkdir -p /app/data

# Set permissions for entrypoint script
RUN chmod +x /app/docker-entrypoint.sh

# Expose port 8000 for Django development server
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command: run development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

#############################################
# Production Stage: Minimal, optimized
#############################################
FROM base as production

# Production-only labels
LABEL maintainer="bart@mosaicmeshai.com"
LABEL version="1.0.0"
LABEL description="StartupWebApp Django Backend - Production"

# Copy only necessary files (no tests, no development tools)
COPY StartupWebApp/ /app/

# Set production settings by default
ENV DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production

# Health check for ECS
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection()" || exit 1

# Expose port 8000 for Django application
EXPOSE 8000

# Production command: gunicorn (will be overridden for migrations)
# Note: For migrations, ECS task definition will override with: ["python", "manage.py", "migrate"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "StartupWebApp.wsgi:application"]
