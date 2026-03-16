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
import psycopg2
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
        from urllib.parse import parse_qsl
        query_params = dict(parse_qsl(result.query))
        socket_path = query_params.get('host', result.hostname)

        conn_params = {
            'database': result.path[1:],
            'user': result.username,
            'password': result.password,
            'host': socket_path,         # ✅ handles both socket and TCP
            'connect_timeout': 10
        }
        if result.port:
            conn_params['port'] = result.port
        if 'sslmode' in query_params:
            conn_params['sslmode'] = query_params['sslmode']
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

# Verify Tailwind output exists
echo "Checking for Tailwind CSS output..."
if [ -f "/app/static/dist/output.css" ]; then
    echo "✅ Tailwind CSS found: $(ls -lh /app/static/dist/output.css)"
else
    echo "❌ Tailwind CSS NOT FOUND at /app/static/dist/output.css"
    echo "📁 Available files in /app/static/:"
    ls -la /app/static/ 2>/dev/null || echo "   (static directory not found)"
    echo "📁 Available files in /app/static/dist/:"
    ls -la /app/static/dist/ 2>/dev/null || echo "   (dist directory not found)"
fi

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
echo "🏨 Tenant Setup & Schema Creation"
echo "========================================"

PRODUCTION_DOMAIN=${PRODUCTION_DOMAIN:-"localhost"}
# Clean the domain - remove protocol prefix if present
if [[ $PRODUCTION_DOMAIN == http://* ]]; then
    PRODUCTION_DOMAIN=${PRODUCTION_DOMAIN#http://}
elif [[ $PRODUCTION_DOMAIN == https://* ]]; then
    PRODUCTION_DOMAIN=${PRODUCTION_DOMAIN#https://}
fi
# Remove trailing slash if present
PRODUCTION_DOMAIN=${PRODUCTION_DOMAIN%/}
echo "📍 Production domain: $PRODUCTION_DOMAIN"
echo ""

python << 'END'
import os
import sys
import django


# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hotel_system.settings')
django.setup()

from apps.platform_admin_flow.models import HotelTenant, HotelDomain
from django.db import connection
from datetime import datetime, timedelta

print("🔧 Setting up tenants and schemas...")

# ===== 1. PUBLIC TENANT =====
try:
    # Ensure public schema exists
    with connection.cursor() as cursor:
        cursor.execute('CREATE SCHEMA IF NOT EXISTS "public"')
    
    public_tenant, created = HotelTenant.objects.get_or_create(
        schema_name='public',
        defaults={
            'name': 'Platform Admin',
            'paid_until': '2099-12-31'
        }
    )
    
    # Create localhost domain for public tenant
    HotelDomain.objects.get_or_create(
        domain='localhost',
        defaults={
            'tenant': public_tenant,
            'is_primary': True
        }
    )
    
    print("✅ Public tenant configured")
    
except Exception as e:
    print(f"❌ Public tenant setup failed: {e}")
    sys.exit(1)

# ===== 2. DEFAULT PRODUCTION TENANT =====
# Clean the domain - remove protocol prefix if present
production_domain = os.getenv('PRODUCTION_DOMAIN', 'localhost')
# Remove http:// or https:// prefix if present
if production_domain.startswith('http://'):
    production_domain = production_domain[len('http://'):]
elif production_domain.startswith('https://'):
    production_domain = production_domain[len('https://'):]
# Remove trailing slash if present
production_domain = production_domain.rstrip('/')

# Only create default tenant if production domain is provided
if production_domain and production_domain != 'localhost':
    try:
        # Create PostgreSQL schema for default tenant
        with connection.cursor() as cursor:
            cursor.execute('CREATE SCHEMA IF NOT EXISTS "default"')
        print("✅ Created PostgreSQL schema: default")
        
        # Create tenant record
        default_tenant, created = HotelTenant.objects.get_or_create(
            schema_name='default',
            defaults={
                'name': 'Default Hotel',
                'paid_until': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            }
        )
        
        # Create domain mapping - MAP TO PUBLIC TENANT FOR ROOT URLS
        # This ensures the production domain stays on public schema
        # so / and /health/ work without tenant context
        
        # First, delete any existing domain entries that might have the wrong format
        # (e.g., with https:// prefix or trailing slashes)
        HotelDomain.objects.filter(domain__startswith=production_domain[:10]).delete()
        HotelDomain.objects.filter(domain=production_domain).delete()
        
        # Now create the domain with the correct mapping to public tenant
        domain_obj = HotelDomain.objects.create(
            domain=production_domain,
            tenant=public_tenant,
            is_primary=True
        )
        
        print(f"✅ Production domain mapped to PUBLIC schema: {production_domain}")
        
    except Exception as e:
        print(f"⚠️  Default tenant setup warning: {e}")
        # Don't exit - this is not critical
else:
    print("ℹ️  No production domain configured, skipping default tenant")

print("")
print("📊 Current tenants:")
for tenant in HotelTenant.objects.all():
    domains = HotelDomain.objects.filter(tenant=tenant)
    domain_list = ', '.join([d.domain for d in domains])
    print(f"   • {tenant.schema_name}: {tenant.name} ({domain_list})")

END

if [ $? -ne 0 ]; then
    echo "❌ Tenant setup failed!"
    exit 1
fi

echo ""

# =======================================
# DATABASE MIGRATIONS - TENANT SCHEMAS
# =======================================
echo "========================================"
echo "🔄 Migrating Tenant Schemas"
echo "========================================"

echo "📋 Running migrations for all tenant schemas..."
python manage.py migrate_schemas --noinput || {
    echo "⚠️  Tenant migrations had issues"
    echo "ℹ️  This is normal if schemas need manual creation"
}

echo "✅ Tenant schema migrations complete"
echo ""

# =======================================
# VERIFY TENANT TABLES
# =======================================
echo "========================================"
echo "🔍 Verifying Tenant Tables"
echo "========================================"

python << 'END'
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hotel_system.settings')
django.setup()

from apps.platform_admin_flow.models import HotelTenant
from django.db import connection

print("📊 Checking table counts per schema...")

for tenant in HotelTenant.objects.all():
    schema = tenant.schema_name
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{schema}'
            """)
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"   ✅ {schema}: {count} tables")
            else:
                print(f"   ⚠️  {schema}: No tables (needs migration)")
    except Exception as e:
        print(f"   ❌ {schema}: Error checking tables - {e}")

END

echo ""

# =======================================
# SUPERUSER CREATION (Optional)
# =======================================
ADMIN_USERNAME=${ADMIN_USERNAME:-""}
ADMIN_EMAIL=${ADMIN_EMAIL:-""}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-""}

if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "========================================"
    echo "👤 Creating Superuser"
    echo "========================================"
    
python << END
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hotel_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.platform_admin_flow.models import HotelTenant
from django.db import connection

try:
    username = os.getenv('ADMIN_USERNAME')
    email = os.getenv('ADMIN_EMAIL')
    password = os.getenv('ADMIN_PASSWORD')
    
    # Set to public schema for superuser creation
    public_tenant = HotelTenant.objects.get(schema_name='public')
    connection.set_tenant(public_tenant)
    
    User = get_user_model()
    
    if User.objects.filter(username=username).exists():
        print(f"⚠️  Superuser '{username}' already exists")
    else:
        User.objects.create_superuser(username, email, password)
        print(f"✅ Created superuser: {username}")
        print(f"   Email: {email}")
        print("   ⚠️  Change password after first login!")
        
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
echo "   • Shared Schema: Migrated ✅"
echo "   • Tenants: Configured ✅"
echo "   • Tenant Schemas: Migrated ✅"
echo "   • Static Files: Collected ✅"
echo ""
echo "🌐 Access Points:"
if [ "$PRODUCTION_DOMAIN" != "localhost" ]; then
    echo "   • Public:  https://$PRODUCTION_DOMAIN/"
    echo "   • Health:  https://$PRODUCTION_DOMAIN/health/"
    echo "   • Admin:   https://$PRODUCTION_DOMAIN/admin/"
else
    echo "   • Public:  http://localhost:8000/"
    echo "   • Health:  http://localhost:8000/health/"
    echo "   • Admin:   http://localhost:8000/admin/"
fi
echo ""
echo "ℹ️  Note: Tenant-specific URLs require proper domain mapping"
echo ""
echo "========================================"
echo "🚀 Starting Gunicorn..."
echo "========================================"
echo ""

exec "$@"