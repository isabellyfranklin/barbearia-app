#!/bin/sh
set -e

echo "Aplicando migrations..."
python manage.py migrate --noinput

exec "$@"
