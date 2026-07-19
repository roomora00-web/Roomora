#!/bin/bash
set -e

# Run database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the application
exec gunicorn staymatch.wsgi:application --workers 4 --threads 8 --worker-class sync --timeout 120 --bind 0.0.0.0:$PORT
