#!/usr/bin/env sh
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

if [ "${DECKS_SEED_DEMO:-0}" = "1" ]; then
  echo "Seeding demo roster (idempotent)..."
  python manage.py seed_demo
  python manage.py seed_history
  python manage.py recompute_scores
fi

if [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ] && [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  echo "Ensuring superuser '${DJANGO_SUPERUSER_USERNAME}'..."
  python manage.py createsuperuser --noinput 2>/dev/null \
    && echo "  superuser created" \
    || echo "  superuser already exists (skipping)"
fi

echo "Starting: $*"
exec "$@"
