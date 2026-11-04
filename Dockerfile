# syntax=docker/dockerfile:1
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

# psycopg[binary] bundles libpq, so no extra system packages are required.
COPY requirements.txt requirements-prod.txt ./
RUN pip install --upgrade pip && pip install -r requirements-prod.txt

COPY . .

# Bake static assets at build time (collectstatic needs no DB connection).
RUN DJANGO_SECRET_KEY=build-only \
    DATABASE_URL=sqlite:////tmp/build.sqlite3 \
    DJANGO_ALLOWED_HOSTS=localhost \
    DJANGO_SECURE_SSL_REDIRECT=false \
    python manage.py collectstatic --noinput

# Run as a non-root user.
RUN useradd --create-home app && chown -R app:app /app
USER app

EXPOSE 8000
ENTRYPOINT ["sh", "./docker/entrypoint.sh"]
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 60"]
