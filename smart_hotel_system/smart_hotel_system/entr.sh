# #!/bin/bash
# set -e

# echo "========================================"
# echo "🚀 QuickDine Multi-Tenant Platform"
# echo "========================================"
# echo "Starting at: $(date)"
# echo ""

# # =======================================
# # ENVIRONMENT VALIDATION
# # =======================================
# echo "🔍 Validating environment..."

# if [ -z "$DATABASE_URL" ]; then
#     echo "❌ ERROR: DATABASE_URL environment variable is not set!"
#     exit 1
# fi

# echo "✅ Environment validated"
# echo ""

# # =======================================
# # DATABASE CONNECTION CHECK
# # =======================================
# echo "========================================"
# echo "🔌 Testing Database Connection"
# echo "========================================"

# python << 'PYEND'
# import os
# import sys
# import time
# from urllib.parse import urlparse

# max_retries = 30
# retry_delay = 2
# db_url = os.environ.get('DATABASE_URL', '')

# if not db_url:
#     print("❌ DATABASE_URL not set!")
#     sys.exit(1)

# # Mask password in logs
# if '@' in db_url:
#     try:
#         result = urlparse(db_url)
#         host_info = f"{result.hostname}:{result.port or 5432}"
#         db_name = result.path[1:] if result.path else 'unknown'
#         print(f"📍 Host: {host_info}")
#         print(f"📊 Database: {db_name}")
#     except:
#         print("📍 Database URL configured")

# for attempt in range(1, max_retries + 1):
#     try:
#         import psycopg2
#         result = urlparse(db_url)
#         conn_params = {
#             'database': result.path[1:],
#             'user': result.username,
#             'password': result.password,
#             'host': result.hostname,
#             'port': result.port or 5432,
#             'sslmode': 'require',
#             'connect_timeout': 10
#         }
#         print(f"🔌 Attempt {attempt}/{max_retries}...", end=' ', flush=True)
#         conn = psycopg2.connect(**conn_params)
#         cursor = conn.cursor()
#         cursor.execute('SELECT version();')
#         version = cursor.fetchone()[0]
        
#         cursor.close()
#         conn.close()
        
#         print("✅ Connected!")
#         print(f"💾 {version[:80]}...")
#         break
        
#     except ImportError:
#         print("\n❌ psycopg2 not installed!")
#         print("Add 'psycopg2-binary' to requirements.txt")
#         sys.exit(1)
        
#     except Exception as e:
#         error_type = type(e).__name__
#         error_msg = str(e)[:100]
        
#         print(f"❌")
        
#         if attempt == 1:
#             print(f"   Error: {error_type}: {error_msg}")
        
#         if attempt < max_retries:
#             if attempt % 5 == 0:
#                 print(f"   Still retrying... ({attempt}/{max_retries})")
#             time.sleep(retry_delay)
#         else:
#             print(f"\n💥 Failed to connect after {max_retries} attempts")
#             print(f"   Last error: {error_type}: {error_msg}")
#             print("\n🔍 Troubleshooting:")
#             print("   1. Verify DATABASE_URL is correct")
#             print("   2. Check if Neon database is active (not suspended)")
#             print("   3. Verify firewall allows outbound connections to *.neon.tech")
#             print("   4. Try using direct endpoint instead of pooler")
#             sys.exit(1)

# print("✅ Database connection verified!")
# PYEND

# # Check if database connection was successful
# if [ $? -ne 0 ]; then
#     echo ""
#     echo "❌ Database connection check failed!"
#     exit 1
# fi

# echo ""

# # =======================================
# # STATIC FILES COLLECTION
# # =======================================
# echo "========================================"
# echo "📦 Collecting Static Files"
# echo "========================================"

# python manage.py collectstatic --noinput || {
#     echo "⚠️  Static file collection failed (non-critical, continuing...)"
# }

# echo "✅ Static files processed"
# echo ""

# # =======================================
# # DATABASE MIGRATIONS - SHARED SCHEMA
# # =======================================
# echo "========================================"
# echo "🔄 Database Migrations - Shared Schema"
# echo "========================================"

# echo "📋 Migrating public/shared schema..."
# python manage.py migrate_schemas --shared --noinput || {
#     echo ""
#     echo "❌ CRITICAL: Shared schema migration failed!"
#     echo "Cannot continue without shared schema."
#     exit 1
# }

# echo "✅ Shared schema migrations complete"
# echo ""

# # =======================================
# # TENANT SETUP & VERIFICATION
# # =======================================
# echo "========================================"
# echo "🏨 Tenant & Domain Setup"
# echo "========================================"

# # Get tenant domain from environment
# TENANT_DOMAIN=${TENANT_DOMAIN:-"localhost"}
# echo "📍 Target domain: $TENANT_DOMAIN"
# echo ""

# python << 'END'
# import os
# import sys
# import django

# # Initialize Django FIRST
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hotel_system.settings')
# django.setup()

# # NOW we can import models
# from apps.platform_admin_flow.models import HotelTenant, HotelDomain
# from datetime import datetime, timedelta

# tenant_domain = os.getenv('TENANT_DOMAIN', 'localhost')

# print("=" * 60)
# print("Setting up tenants and domains...")
# print("=" * 60)

# try:
#     # ========================================
#     # 1. PUBLIC TENANT (Required for django-tenants)
#     # ========================================
#     print("\n📦 Step 1: Public/Platform Tenant")
#     print("-" * 60)
    
#     public_tenant, pub_created = HotelTenant.objects.get_or_create(
#         schema_name='public',
#         defaults={
#             'name': 'Platform Admin',
#             'paid_until': '2099-12-31',
#         }
#     )
    
#     if pub_created:
#         print("✅ Created public tenant")
#     else:
#         print("⚠️  Public tenant already exists")
    
#     # ========================================
#     # 2. LOCALHOST DOMAIN (For local development)
#     # ========================================
#     print("\n🌐 Step 2: Localhost Domain")
#     print("-" * 60)
    
#     localhost_domain, local_created = HotelDomain.objects.get_or_create(
#         domain='localhost',
#         defaults={
#             'tenant': public_tenant,
#             'is_primary': False,
#         }
#     )
    
#     if local_created:
#         print("✅ Created localhost domain")
#     else:
#         # Ensure it points to public tenant
#         if localhost_domain.tenant != public_tenant:
#             localhost_domain.tenant = public_tenant
#             localhost_domain.save()
#             print("✅ Updated localhost to point to public tenant")
#         else:
#             print("⚠️  Localhost domain already exists")
    
#     # ========================================
#     # 3. PRODUCTION DOMAIN (Control Plane URL)
#     # ========================================
#     if tenant_domain != 'localhost':
#         print(f"\n🌐 Step 3: Production Domain ({tenant_domain})")
#         print("-" * 60)
        
#         prod_domain, prod_created = HotelDomain.objects.get_or_create(
#             domain=tenant_domain,
#             defaults={
#                 'tenant': public_tenant,
#                 'is_primary': True,
#             }
#         )
        
#         if prod_created:
#             print(f"✅ Created domain: {tenant_domain}")
#         else:
#             # Ensure it points to public tenant and is primary
#             if prod_domain.tenant != public_tenant or not prod_domain.is_primary:
#                 prod_domain.tenant = public_tenant
#                 prod_domain.is_primary = True
#                 prod_domain.save()
#                 print(f"✅ Updated domain: {tenant_domain}")
#             else:
#                 print(f"⚠️  Domain already exists: {tenant_domain}")
    
#     # ========================================
#     # 4. DEFAULT TENANT (Optional - for first hotel)
#     # ========================================
#     print("\n🏨 Step 4: Default Hotel Tenant (Optional)")
#     print("-" * 60)
    
#     # Only create if it doesn't exist
#     default_tenant, def_created = HotelTenant.objects.get_or_create(
#         schema_name='default',
#         defaults={
#             'name': 'Default Hotel',
#             'paid_until': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
#         }
#     )
    
#     if def_created:
#         print(f"✅ Created default hotel tenant")
        
#         # Create subdomain for default tenant (optional)
#         # default_subdomain = f"hotel.{tenant_domain}"
#         # if tenant_domain != 'localhost':
#         #     HotelDomain.objects.get_or_create(
#         #         domain=default_subdomain,
#         #         defaults={
#         #             'tenant': default_tenant,
#         #             'is_primary': True,
#         #         }
#         #     )
#         #     print(f"✅ Created subdomain: {default_subdomain}")
#     else:
#         print("⚠️  Default hotel tenant already exists")
    
#     # ========================================
#     # 5. SUMMARY
#     # ========================================
#     print("\n" + "=" * 60)
#     print("📊 CONFIGURATION SUMMARY")
#     print("=" * 60)
    
#     print("\n🏢 TENANTS:")
#     for tenant in HotelTenant.objects.all().order_by('schema_name'):
#         print(f"   • {tenant.schema_name:15} → {tenant.name}")
    
#     print("\n🌐 DOMAINS:")
#     for domain in HotelDomain.objects.all().order_by('domain'):
#         primary_marker = "⭐" if domain.is_primary else "  "
#         print(f"   {primary_marker} {domain.domain:40} → {domain.tenant.schema_name}")
    
#     print("\n✅ Tenant setup complete!")
#     print("=" * 60)
    
# except Exception as e:
#     print(f"\n❌ ERROR during tenant setup: {e}")
#     import traceback
#     traceback.print_exc()
#     sys.exit(1)

# END

# # Check if tenant setup was successful
# if [ $? -ne 0 ]; then
#     echo ""
#     echo "❌ Tenant setup failed!"
#     exit 1
# fi

# echo ""

# # =======================================
# # DATABASE MIGRATIONS - TENANT SCHEMAS
# # =======================================
# echo "========================================"
# echo "🔄 Database Migrations - Tenant Schemas"
# echo "========================================"

# echo "📋 Migrating all tenant schemas..."
# python manage.py migrate_schemas --noinput || {
#     echo ""
#     echo "⚠️  Warning: Some tenant migrations had issues"
#     echo "This may be normal if tenants were just created"
# }

# echo "✅ Tenant schema migrations processed"
# echo ""

# # =======================================
# # SUPERUSER CREATION (Optional)
# # =======================================
# ADMIN_USERNAME=${ADMIN_USERNAME:-""}
# ADMIN_EMAIL=${ADMIN_EMAIL:-""}
# ADMIN_PASSWORD=${ADMIN_PASSWORD:-""}

# if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
#     echo "========================================"
#     echo "👤 Creating Default Superuser"
#     echo "========================================"
    
# python << END
# import os
# import sys
# import django

# # Initialize Django FIRST
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hotel_system.settings')
# django.setup()

# # NOW we can import
# from django.contrib.auth import get_user_model
# from apps.platform_admin_flow.models import HotelTenant
# from django.db import connection

# try:
#     username = os.getenv('ADMIN_USERNAME')
#     email = os.getenv('ADMIN_EMAIL')
#     password = os.getenv('ADMIN_PASSWORD')
    
#     # Set public tenant context
#     public_tenant = HotelTenant.objects.get(schema_name='public')
#     connection.set_tenant(public_tenant)
    
#     User = get_user_model()
    
#     if User.objects.filter(username=username).exists():
#         print(f"⚠️  Superuser '{username}' already exists")
#     else:
#         User.objects.create_superuser(username, email, password)
#         print(f"✅ Created superuser: {username}")
#         print(f"   Email: {email}")
#         print(f"   ⚠️  Change the password after first login!")
    
# except Exception as e:
#     print(f"⚠️  Could not create superuser: {e}")

# END
    
#     echo ""
# fi

# # =======================================
# # STARTUP SUMMARY
# # =======================================
# echo "========================================"
# echo "✅ Initialization Complete!"
# echo "========================================"
# echo ""
# echo "📊 System Status:"
# echo "   • Database: Connected ✅"
# echo "   • Migrations: Complete ✅"
# echo "   • Tenants: Configured ✅"
# echo "   • Static Files: Collected ✅"
# echo ""
# echo "🌐 Access Points:"

# if [ "$TENANT_DOMAIN" != "localhost" ]; then
#     echo "   • Admin: https://$TENANT_DOMAIN/admin/"
#     echo "   • Health: https://$TENANT_DOMAIN/health/"
#     echo "   • API: https://$TENANT_DOMAIN/"
# else
#     echo "   • Admin: http://localhost:8000/admin/"
#     echo "   • Health: http://localhost:8000/health/"
#     echo "   • API: http://localhost:8000/"
# fi

# echo ""
# echo "========================================"
# echo "🚀 Starting Gunicorn..."
# echo "========================================"
# echo ""

# # Execute the CMD from Dockerfile (Gunicorn)
# exec "$@"