release: python manage.py migrate --noinput
web: gunicorn staymatch.wsgi:application --workers 4 --threads 8 --worker-class sync --timeout 120 --bind 0.0.0.0:$PORT
worker: celery -A staymatch worker --loglevel=info --concurrency=2
