#!/bin/sh
set -e

echo "Aplicando migrations..."
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
