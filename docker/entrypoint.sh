#!/usr/bin/env sh
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Starting: $*"
exec "$@"
