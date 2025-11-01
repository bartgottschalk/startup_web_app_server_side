# Dockerfile for StartupWebApp Backend - Development Environment
# Python 3.12 + Django 2.2 + SQLite

FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files (includes docker-entrypoint.sh)
COPY StartupWebApp/ /app/

# Create directory for SQLite database
RUN mkdir -p /app/data

# Set permissions for entrypoint script
RUN chmod +x /app/docker-entrypoint.sh

# Expose port 8000 for Django development server
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command: run development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
