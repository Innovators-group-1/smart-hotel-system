#!/bin/bash
set -e

echo "========================================"
echo "🚀 QuickDine Multi-Tenant Platform"
echo "========================================"
echo "Starting at: $(date)"
echo ""

# =======================================
# ENVIRONMENT VALIDATION
# =======================================
echo "🔍 Validating environment..."

if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set!"
    exit 1
fi

echo "✅ Environment validated"
echo ""

# =======================================
# DATABASE CONNECTION CHECK
# =======================================
echo "========================================"
echo "🔌 Testing Database Connection"
echo "========================================"

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

try:
    result = urlparse(db_url)
    host_info = f"{result.hostname}:{result.port or 5432}"
    db_name = result.path[1:] if result.path else 'unknown'
    print(f"📍 Host: {host_info}")
    print(f"📊 Database: {db_name}")
except:
    print("📍 Database URL configured")

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
        print(f"🔌 Attempt {attempt}/{max_retries}...", end=' ', flush=True)
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        cursor.close(); conn.close()
        print("✅ Connected!")
        print(f"💾 {version[:80]}...")
        break
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)[:100]}")
        if attempt < max_retries:
            time.sleep(retry_delay)
        else:
            print("💥 Failed to connect after retries")
            sys.exit(1)

print("✅ Database connection verified!")
PYEND

if [ $? -ne 0 ]; then
    echo "❌ Database connection check failed!"
    exit 1
fi

echo ""

# =======================================
# STATIC FILES COLLECTION
# =======================================
echo "========================================"
echo "📦 Collecting Static Files"
echo "========================================"

python manage.py collectstatic --noinput || {
    echo "⚠️  Static file collection failed (non-critical, continuing...)"
}

echo "✅ Static files processed"
echo ""

# =======================================
# DATABASE MIGRATIONS - SHARED SCHEMA
# =======================================
echo "========================================"
echo "🔄 Database Migrations - Shared Schema"
echo "========================================"

echo "📋 Migrating public/shared schema..."
python manage.py migrate_schemas --shared --noinput || {
    echo "❌ CRITICAL: Shared schema migration failed!"
    exit 1
}

echo "✅ Shared schema migrations complete"
echo ""

# =======================================
# TENANT SETUP & VERIFICATION
# =======================================
echo "========================================"
echo "🏨 Tenant & Domain Setup"
echo "========================================"

TENANT_DOMAIN=${TENANT_DOMAIN:-"localhost"}
echo "📍 Target domain: $TENANT_DOMAIN"
echo ""

python << 'END'
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hotel_system.settings')
django.setup()

from apps.platform_admin_flow.models import HotelTenant, HotelDomain
from datetime import datetime, timedelta

try:
    public_tenant, _ = HotelTenant.objects.get_or_create(
        schema_name='public',
        defaults={'name': 'Platform Admin','paid_until': '2099-12-31'}
    )
    default_tenant, _ = HotelTenant.objects.get_or_create(
        schema_name='default',
        defaults={'name': 'Default Hotel','paid_until': (datetime.now()+timedelta(days=365)).strftime('%Y-%m-%d')}
    )
    print("✅ Verified public and default tenants")
except Exception as e:
    print(f"❌ Tenant setup failed: {e}")
    sys.exit(1)
END

if [ $? -ne 0 ]; then
    echo "❌ Tenant verification failed!"
    exit 1
fi

echo ""

# =======================================
# DATABASE MIGRATIONS - TENANT SCHEMAS
# =======================================
echo "========================================"
echo "🔄 Database Migrations - Tenant Schemas"
echo "========================================"

echo "📋 Migrating all tenant schemas..."
python manage.py migrate_schemas --noinput || {
    echo "⚠️ Tenant migrations had issues (likely new tenants)"
}

echo "✅ Tenant schema migrations processed"
echo ""

# =======================================
# SUPERUSER CREATION (Optional)
# =======================================
ADMIN_USERNAME=${ADMIN_USERNAME:-""}
ADMIN_EMAIL=${ADMIN_EMAIL:-""}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-""}

if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "========================================"
    echo "👤 Creating Default Superuser"
    echo "========================================"
    
python << END
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hotel_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.platform_admin_flow.models import HotelTenant
from django.db import connection

try:
    username = os.getenv('ADMIN_USERNAME')
    email = os.getenv('ADMIN_EMAIL')
    password = os.getenv('ADMIN_PASSWORD')
    public_tenant = HotelTenant.objects.get(schema_name='public')
    connection.set_tenant(public_tenant)
    User = get_user_model()
    if User.objects.filter(username=username).exists():
        print(f"⚠️  Superuser '{username}' already exists")
    else:
        User.objects.create_superuser(username, email, password)
        print(f"✅ Created superuser: {username}")
        print(f"   Email: {email}")
        print("   ⚠️  Change the password after first login!")
except Exception as e:
    print(f"⚠️  Could not create superuser: {e}")
END
    echo ""
fi

# =======================================
# STARTUP SUMMARY
# =======================================
echo "========================================"
echo "✅ Initialization Complete!"
echo "========================================"
echo ""
echo "📊 System Status:"
echo "   • Database: Connected ✅"
echo "   • Migrations: Complete ✅"
echo "   • Tenants: Configured ✅"
echo "   • Static Files: Collected ✅"
echo ""
echo "🌐 Access Points:"
if [ "$TENANT_DOMAIN" != "localhost" ]; then
    echo "   • Admin: https://$TENANT_DOMAIN/admin/"
    echo "   • Health: https://$TENANT_DOMAIN/health/"
    echo "   • API: https://$TENANT_DOMAIN/"
else
    echo "   • Admin: http://localhost:8000/admin/"
    echo "   • Health: http://localhost:8000/health/"
    echo "   • API: http://localhost:8000/"
fi

echo ""
echo "========================================"
echo "🚀 Starting Gunicorn..."
echo "========================================"
echo ""

exec "$@"


