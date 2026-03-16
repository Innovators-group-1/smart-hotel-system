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
        # New arguments for creating any tenant non-interactively
        parser.add_argument(
            '--schema',
            type=str,
            help='Schema name for a custom tenant (e.g. calvidas)',
            default=None,
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Display name for the custom tenant (e.g. Calvidas Hotel)',
            default=None,
        )
        parser.add_argument(
            '--tenant-domain',
            type=str,
            help='Domain for the custom tenant (e.g. calvidas.quickdine.ink)',
            default=None,
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
            
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                cursor.execute(f'CREATE SCHEMA "{schema_name}"')
                self.stdout.write(f'   🧹 Ensured clean schema')
            
            migration_output = StringIO()
            
            call_command(
                'migrate_schemas', 
                schema=schema_name, 
                verbosity=1,
                stdout=migration_output,
                stderr=migration_output
            )
            
            output = migration_output.getvalue()
            if output:
                lines = [l.strip() for l in output.split('\n') if l.strip()]
                for line in lines[-5:]:
                    self.stdout.write(f'   {line}')
            
            self.stdout.write(self.style.SUCCESS(f'✅ Migrated schema: {schema_name}'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Migration failed for {schema_name}'))
            error_msg = str(e)
            self.stdout.write(self.style.ERROR(f'   Error: {error_msg[:300]}'))
            
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
        
        if not self.create_postgres_schema(schema_name):
            return False
        
        try:
            with transaction.atomic():
                tenant = HotelTenant.objects.create(
                    schema_name=schema_name,
                    name=tenant_name,
                    paid_until=paid_until,
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Created tenant record: {tenant.name}'))
                
                domain = HotelDomain.objects.create(
                    domain=domain_name_input,
                    tenant=tenant,
                    is_primary=True,
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Created domain: {domain.domain}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating tenant record: {e}'))
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            self.stdout.write(self.style.WARNING(f'⚠️  Rolled back schema: {schema_name}'))
            return False
        
        if not self.migrate_tenant_schema(schema_name):
            self.stdout.write(self.style.WARNING(f'⚠️  Cleaning up tenant records for {schema_name}'))
            HotelTenant.objects.filter(schema_name=schema_name).delete()
            return False
        
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
        custom_schema = options.get('schema')
        custom_name = options.get('name')
        custom_tenant_domain = options.get('tenant_domain')

        # ==========================================
        # 1. Create Public/Platform Admin Tenant
        # ==========================================
        self.stdout.write(self.style.NOTICE('Setting up public schema...'))
        
        self.create_postgres_schema('public')
        
        public_tenant, created = HotelTenant.objects.get_or_create(
            schema_name='public',
            defaults={
                'name': 'Platform Admin',
                'paid_until': '2099-12-31',
            }
        )
        
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
        # 2. Create Custom Tenant (new --schema flag)
        # ==========================================
        if custom_schema and custom_name and custom_tenant_domain:
            if HotelTenant.objects.filter(schema_name=custom_schema).exists():
                self.stdout.write(self.style.WARNING(f'⚠️  Tenant "{custom_schema}" already exists'))
            elif HotelDomain.objects.filter(domain=custom_tenant_domain).exists():
                self.stdout.write(self.style.WARNING(f'⚠️  Domain "{custom_tenant_domain}" already exists'))
            else:
                paid_until = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
                self.create_complete_tenant(custom_schema, custom_name, paid_until, custom_tenant_domain)

        # ==========================================
        # 3. Create Default Production Tenant
        # ==========================================
        elif not interactive:
            if domain_name != 'localhost':
                if HotelTenant.objects.filter(schema_name='default').exists():
                    self.stdout.write(self.style.WARNING('⚠️  Default tenant already exists'))
                else:
                    paid_until = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
                    self.create_complete_tenant('default', 'Default Hotel', paid_until, domain_name)

        # ==========================================
        # 4. Interactive Mode
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
                
                domain_name_input = input(f'Domain (e.g., {schema_name}.quickdine.ink): ').strip()
                if not domain_name_input:
                    self.stdout.write(self.style.ERROR('Domain required.'))
                    continue
                
                if HotelDomain.objects.filter(domain=domain_name_input).exists():
                    self.stdout.write(self.style.ERROR(f'Domain "{domain_name_input}" exists.'))
                    continue

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
        # 5. Summary
        # ==========================================
        self.stdout.write(self.style.NOTICE('\n' + '='*50))
        self.stdout.write(self.style.NOTICE('Final Summary'))
        self.stdout.write(self.style.NOTICE('='*50))
        
        tenants = HotelTenant.objects.all()
        for tenant in tenants:
            domains = HotelDomain.objects.filter(tenant=tenant)
            self.stdout.write(f'\n📦 {tenant.name}')
            self.stdout.write(f'   Schema: {tenant.schema_name}')
            self.stdout.write(f'   Domains: {", ".join([d.domain for d in domains])}')
        
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
