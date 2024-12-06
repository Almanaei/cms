web: gunicorn -c gunicorn_config.py "app:create_app('production')"
worker: celery -A app.celery worker --loglevel=info
beat: celery -A app.celery beat --loglevel=info
