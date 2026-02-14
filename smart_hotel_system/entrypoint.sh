#!/bin/sh

echo "Running shared migrations..."
python manage.py migrate_schemas --shared --noinput

echo "Running tenant migrations..."
python manage.py migrate_schemas --tenant --noinput

echo "Starting server..."
exec "$@"
