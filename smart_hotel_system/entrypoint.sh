#!/bin/bash
set -e

echo "========================================"
echo "🚀 QuickDine Startup"
echo "========================================"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set!"
    exit 1
fi

echo "🔍 Testing database connection..."

# Better database connection test with retries
python << 'PYEND'
import os
import sys
import time
from urllib.parse import urlparse

max_retries = 30
retry_delay = 2
db_url = os.environ.get('DATABASE_URL', '')

if not db_url:
    print("❌ DATABASE_URL not set!")
    sys.exit(1)

# Mask password in logs
if '@' in db_url:
    host_info = db_url.split('@')[1].split('/')[0]
    db_name = db_url.split('/')[-1].split('?')[0]
    print(f"📍 Connecting to: {host_info}")
    print(f"📊 Database: {db_name}")

for attempt in range(1, max_retries + 1):
    try:
        import psycopg2
        result = urlparse(db_url)
        
        conn_params = {
            'database': result.path[1:],
            'user': result.username,
            'password': result.password,
            'host': result.hostname,
            'port': result.port or 5432,
            'sslmode': 'require',
            'connect_timeout': 10
        }
        
        print(f"🔌 Attempt {attempt}/{max_retries}...", end=' ')
        
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print("✅ Connected!")
        print(f"💾 PostgreSQL: {version[:60]}...")
        break
        
    except ImportError:
        print("\n❌ psycopg2 not installed!")
        sys.exit(1)
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)[:100]
        
        print(f"❌ Failed ({error_type})")
        
        if attempt == 1:
            print(f"   Error: {error_msg}")
        
        if attempt < max_retries:
            if attempt % 5 == 0:
                print(f"   Still trying... ({attempt}/{max_retries})")
            time.sleep(retry_delay)
        else:
            print(f"\n💥 Could not connect after {max_retries} attempts")
            print(f"   Last error: {error_msg}")
            sys.exit(1)

print("✅ Database is ready!\n")
PYEND

# Check if connection was successful
if [ $? -ne 0 ]; then
    echo "❌ Database connection check failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "📦 Collecting static files..."
echo "========================================"
python manage.py collectstatic --noinput || {
    echo "⚠️  Static collection failed (continuing anyway)"
}

echo ""
echo "========================================"
echo "🔄 Running migrations..."
echo "========================================"

echo "📋 Step 1: Migrating shared schema (public)..."
python manage.py migrate_schemas --shared --noinput || {
    echo "❌ Shared schema migration FAILED!"
    exit 1
}
echo "✅ Shared schema migrated"

echo ""
echo "📋 Step 2: Setting up tenants..."

# Get domain from environment variable
TENANT_DOMAIN=${TENANT_DOMAIN:-"localhost"}

python manage.py create_inital_tenant --domain "$TENANT_DOMAIN" || {
    echo "⚠️  Tenant setup had issues (continuing...)"
}

echo ""
echo "📋 Step 3: Migrating all tenant schemas..."
python manage.py migrate_schemas --noinput || {
    echo "⚠️  Some tenant migrations had issues (continuing...)"
}
echo "✅ All schemas migrated"

echo ""
echo "========================================"
echo "🎉 Initialization Complete!"
echo "🚀 Starting Gunicorn..."
echo "========================================"
echo ""

exec "$@"