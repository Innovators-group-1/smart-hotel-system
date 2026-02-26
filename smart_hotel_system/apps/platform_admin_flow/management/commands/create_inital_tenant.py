from django.core.management.base import BaseCommand
from django.db import connection, transaction
from apps.platform_admin_flow.models import HotelTenant, HotelDomain
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Set up public schema and create default tenant for deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Domain name for the default tenant',
            default='localhost',
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Run in interactive mode to create multiple tenants',
        )

    def create_postgres_schema(self, schema_name):
        """Create PostgreSQL schema if it doesn't exist"""
        with connection.cursor() as cursor:
            try:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                self.stdout.write(self.style.SUCCESS(f'✅ Created PostgreSQL schema: {schema_name}'))
                return True
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to create schema {schema_name}: {e}'))
                return False

    def migrate_tenant_schema(self, schema_name):
        """Run migrations for a specific tenant schema with guaranteed clean state"""
        from django.core.management import call_command
        from io import StringIO
        
        try:
            self.stdout.write(f'🔄 Running migrations for schema: {schema_name}...')
            
            # CRITICAL FIX: Drop and recreate schema to ensure clean state
            # This prevents duplicate key errors from partial migrations
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                cursor.execute(f'CREATE SCHEMA "{schema_name}"')
                self.stdout.write(f'   🧹 Ensured clean schema')
            
            # Capture migration output
            migration_output = StringIO()
            
            # Run migrations
            call_command(
                'migrate_schemas', 
                schema=schema_name, 
                verbosity=1,
                stdout=migration_output,
                stderr=migration_output
            )
            
            # Show condensed migration output
            output = migration_output.getvalue()
            if output:
                lines = [l.strip() for l in output.split('\n') if l.strip()]
                # Show only important lines
                for line in lines[-5:]:  # Last 5 lines usually show completion
                    self.stdout.write(f'   {line}')
            
            self.stdout.write(self.style.SUCCESS(f'✅ Migrated schema: {schema_name}'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Migration failed for {schema_name}'))
            error_msg = str(e)
            # Show first 300 chars of error
            self.stdout.write(self.style.ERROR(f'   Error: {error_msg[:300]}'))
            
            # Rollback: Drop the schema
            self.stdout.write(self.style.WARNING(f'⚠️  Rolling back schema: {schema_name}'))
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                self.stdout.write(self.style.SUCCESS(f'✅ Rolled back schema: {schema_name}'))
            except Exception as rollback_error:
                self.stdout.write(self.style.ERROR(f'Failed to rollback: {rollback_error}'))
            
            return False

    def create_complete_tenant(self, schema_name, tenant_name, paid_until, domain_name_input):
        """Create tenant with schema, record, domain, and migrations - all in one"""
        
        self.stdout.write(self.style.NOTICE(f'\n🏗️  Creating tenant: {tenant_name}'))
        
        # Step 1: Create PostgreSQL schema (will be recreated during migration)
        if not self.create_postgres_schema(schema_name):
            return False
        
        # Step 2: Create tenant record (with rollback on failure)
        try:
            with transaction.atomic():
                tenant = HotelTenant.objects.create(
                    schema_name=schema_name,
                    name=tenant_name,
                    paid_until=paid_until,
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Created tenant record: {tenant.name}'))
                
                # Create domain
                domain = HotelDomain.objects.create(
                    domain=domain_name_input,
                    tenant=tenant,
                    is_primary=True,
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Created domain: {domain.domain}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating tenant record: {e}'))
            # Rollback: Drop schema
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            self.stdout.write(self.style.WARNING(f'⚠️  Rolled back schema: {schema_name}'))
            return False
        
        # Step 3: Run migrations (schema will be cleaned and recreated inside this method)
        if not self.migrate_tenant_schema(schema_name):
            # Delete tenant and domain records if migration fails
            self.stdout.write(self.style.WARNING(f'⚠️  Cleaning up tenant records for {schema_name}'))
            HotelTenant.objects.filter(schema_name=schema_name).delete()
            return False
        
        # Step 4: Verify tables were created
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{schema_name}'
            """)
            table_count = cursor.fetchone()[0]
            self.stdout.write(f'   📊 Created {table_count} tables')
        
        self.stdout.write(self.style.SUCCESS(f'🎉 Successfully created complete tenant: {tenant_name}\n'))
        return True

    def handle(self, *args, **options):
        domain_name = options['domain']
        interactive = options['interactive']

        # ==========================================
        # 1. Create Public/Platform Admin Tenant
        # ==========================================
        self.stdout.write(self.style.NOTICE('Setting up public schema...'))
        
        # Ensure public schema exists
        self.create_postgres_schema('public')
        
        public_tenant, created = HotelTenant.objects.get_or_create(
            schema_name='public',
            defaults={
                'name': 'Platform Admin',
                'paid_until': '2099-12-31',
            }
        )
        
        # Create localhost domain for public schema
        public_domain, public_domain_created = HotelDomain.objects.get_or_create(
            domain='localhost',
            defaults={
                'tenant': public_tenant,
                'is_primary': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created Platform Admin tenant'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Platform Admin tenant already exists'))
        
        if public_domain_created:
            self.stdout.write(self.style.SUCCESS('✅ Created localhost domain'))

        # ==========================================
        # 2. Create Default Production Tenant
        # ==========================================
        if not interactive:
            if domain_name != 'localhost':
                # Check if default tenant already exists
                if HotelTenant.objects.filter(schema_name='default').exists():
                    self.stdout.write(self.style.WARNING('⚠️  Default tenant already exists'))
                else:
                    paid_until = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
                    self.create_complete_tenant('default', 'Default Hotel', paid_until, domain_name)

        # ==========================================
        # 3. Interactive Mode
        # ==========================================
        if interactive:
            self.stdout.write(self.style.NOTICE('\n' + '='*50))
            self.stdout.write(self.style.NOTICE('Interactive Tenant Creation'))
            self.stdout.write(self.style.NOTICE('='*50 + '\n'))

            while True:
                self.stdout.write(self.style.NOTICE("Creating a new tenant..."))

                schema_name = input('Enter schema name or "exit": ').strip()
                if schema_name.lower() == 'exit':
                    break
                
                if not schema_name or ' ' in schema_name:
                    self.stdout.write(self.style.ERROR('Invalid schema name.'))
                    continue
                
                if HotelTenant.objects.filter(schema_name=schema_name).exists():
                    self.stdout.write(self.style.ERROR(f'Tenant "{schema_name}" already exists.'))
                    continue
                
                tenant_name = input('Enter tenant name: ').strip()
                if not tenant_name:
                    self.stdout.write(self.style.ERROR('Tenant name required.'))
                    continue
                
                paid_until = input('Paid until (YYYY-MM-DD, default 1 year): ').strip()
                if not paid_until:
                    paid_until = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
                
                domain_name_input = input(f'Domain (e.g., {schema_name}.localhost): ').strip()
                if not domain_name_input:
                    self.stdout.write(self.style.ERROR('Domain required.'))
                    continue
                
                if HotelDomain.objects.filter(domain=domain_name_input).exists():
                    self.stdout.write(self.style.ERROR(f'Domain "{domain_name_input}" exists.'))
                    continue

                # Create complete tenant
                success = self.create_complete_tenant(
                    schema_name, 
                    tenant_name, 
                    paid_until, 
                    domain_name_input
                )
                
                if not success:
                    self.stdout.write(self.style.ERROR('❌ Failed. Try again.\n'))
                    continue

                another = input('Create another? (yes/no): ').strip().lower()
                if another not in ['yes', 'y']:
                    break

        # ==========================================
        # 4. Summary
        # ==========================================
        self.stdout.write(self.style.NOTICE('\n' + '='*50))
        self.stdout.write(self.style.NOTICE('Final Summary'))
        self.stdout.write(self.style.NOTICE('='*50))
        
        # Show tenants
        tenants = HotelTenant.objects.all()
        for tenant in tenants:
            domains = HotelDomain.objects.filter(tenant=tenant)
            self.stdout.write(f'\n📦 {tenant.name}')
            self.stdout.write(f'   Schema: {tenant.schema_name}')
            self.stdout.write(f'   Domains: {", ".join([d.domain for d in domains])}')
        
        # Show PostgreSQL schemas with table counts
        self.stdout.write(self.style.NOTICE('\n' + '='*50))
        self.stdout.write(self.style.NOTICE('PostgreSQL Schemas'))
        self.stdout.write(self.style.NOTICE('='*50))
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.schema_name,
                    COUNT(t.table_name) as table_count
                FROM information_schema.schemata s
                LEFT JOIN information_schema.tables t 
                    ON s.schema_name = t.table_schema
                WHERE s.schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                GROUP BY s.schema_name
                ORDER BY s.schema_name
            """)
            for row in cursor.fetchall():
                self.stdout.write(f'   - {row[0]}: {row[1]} tables')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Setup complete! Total tenants: {tenants.count()}'))