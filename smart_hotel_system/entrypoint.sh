#!/bin/bash
set -e

echo "========================================"
echo "🚀 QuickDine Startup"
echo "========================================"

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput || {
    echo "⚠️ Static collection failed, continuing..."
}

echo ""
echo "========================================"
echo "🔄 Running migrations..."
echo "========================================"

# IMPORTANT: Run migrations WITHOUT the --shared flag first
# This creates the base Django tables
echo "📋 Creating base Django tables..."
python manage.py migrate --run-syncdb || {
    echo "❌ Initial migration failed!"
    exit 1
}

echo ""
echo "📋 Running shared schema migrations..."
python manage.py migrate_schemas --shared --noinput || {
    echo "❌ Shared schema migration FAILED!"
    exit 1
}

echo ""
echo "📋 Running tenant schema migrations..."
python manage.py migrate_schemas --tenant --noinput || {
    echo "⚠️ Tenant migration had issues"
}

echo ""
echo "========================================"
echo "🎉 Initialization Complete!"
echo "🚀 Starting Gunicorn..."
echo "========================================"

exec "$@"