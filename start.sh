#!/bin/bash
set -e

# Force cache invalidation and clean start
echo "Starting deployment setup for Roomora..."

# Run database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the application
exec gunicorn staymatch.wsgi:application --workers 2 --threads 4 --worker-class gthread --timeout 120 --bind 0.0.0.0:${PORT:-8080}
