#!/bin/bash
# Entrypoint script for StartupWebApp Backend

set -e

echo "========================================"
echo "StartupWebApp Backend - Starting"
echo "========================================"

# Wait a moment for any dependencies (future: database)
sleep 2

# Check if database exists, if not run migrations
if [ ! -f "/app/data/db.sqlite3" ]; then
    echo "Database not found. Running initial migrations..."
    python manage.py migrate --noinput

    echo ""
    echo "========================================"
    echo "Database initialized!"
    echo "========================================"
    echo ""
    echo "To create a superuser for Django Admin, run:"
    echo "  docker-compose exec backend python manage.py createsuperuser"
    echo ""
else
    echo "Database found. Running any pending migrations..."
    python manage.py migrate --noinput
fi

echo ""
echo "========================================"
echo "Starting Django development server..."
echo "========================================"
echo "API available at: http://localhost:8000"
echo "Django Admin at: http://localhost:8000/admin/"
echo ""
echo "Available API endpoints:"
echo "  - http://localhost:8000/user/logged-in"
echo "  - http://localhost:8000/order/products"
echo "  - http://localhost:8000/clientevent/pageview"
echo ""
echo "Press CTRL+C to stop"
echo "========================================"
echo ""

# Execute the main command (from CMD in Dockerfile or docker-compose)
exec "$@"
