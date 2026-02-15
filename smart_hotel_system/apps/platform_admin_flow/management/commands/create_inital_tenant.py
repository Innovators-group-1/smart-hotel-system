from django.core.management.base import BaseCommand
from django.db import connection
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

    def handle(self, *args, **options):
        domain_name = options['domain']
        interactive = options['interactive']

        # ==========================================
        # 1. Create Public/Platform Admin Tenant
        # ==========================================
        self.stdout.write(self.style.NOTICE('Setting up public schema...'))
        
        public_tenant, created = HotelTenant.objects.get_or_create(
            schema_name='public',
            defaults={
                'name': 'Platform Admin',
                'paid_until': '2099-12-31',  # Far future date
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
            self.stdout.write(self.style.NOTICE(f'\nCreating default tenant for domain: {domain_name}'))
            
            # Skip if domain is localhost (already handled above)
            if domain_name != 'localhost':
                tenant, tenant_created = HotelTenant.objects.get_or_create(
                    schema_name='default',
                    defaults={
                        'name': 'Default Hotel',
                        'paid_until': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
                    }
                )
                
                domain, domain_created = HotelDomain.objects.get_or_create(
                    domain=domain_name,
                    defaults={
                        'tenant': tenant,
                        'is_primary': True,
                    }
                )

                if tenant_created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created tenant: {tenant.name}'))
                    self.stdout.write(self.style.SUCCESS(f'   Schema: {tenant.schema_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️  Tenant already exists: {tenant.name}'))
                
                if domain_created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created domain: {domain_name}'))
                else:
                    # Update domain if it exists but points to different tenant
                    if domain.tenant != tenant:
                        domain.tenant = tenant
                        domain.save()
                        self.stdout.write(self.style.SUCCESS(f'✅ Updated domain to point to {tenant.name}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠️  Domain already exists: {domain_name}'))

        # ==========================================
        # 3. Interactive Mode (for local development)
        # ==========================================
        if interactive:
            self.stdout.write(self.style.NOTICE('\n' + '='*50))
            self.stdout.write(self.style.NOTICE('Interactive Tenant Creation'))
            self.stdout.write(self.style.NOTICE('='*50 + '\n'))

            while True:
                self.stdout.write(self.style.NOTICE("Creating a new tenant..."))

                # Get schema name
                schema_name = input('Enter schema name (e.g., "calvidas_hotel") or "exit" to stop: ').strip()
                if schema_name.lower() == 'exit':
                    break
                
                # Validate schema name
                if not schema_name or ' ' in schema_name:
                    self.stdout.write(self.style.ERROR('Schema name cannot be empty or contain spaces.'))
                    continue
                
                # Check if schema already exists
                if HotelTenant.objects.filter(schema_name=schema_name).exists():
                    self.stdout.write(self.style.ERROR(f'Tenant with schema "{schema_name}" already exists.'))
                    continue
                
                # Get tenant name
                tenant_name = input('Enter tenant name (e.g., "Calvidas Hotel"): ').strip()
                if not tenant_name:
                    self.stdout.write(self.style.ERROR('Tenant name cannot be empty.'))
                    continue
                
                # Get paid until date
                paid_until = input('Enter paid until date (YYYY-MM-DD, default: 1 year): ').strip()
                if not paid_until:
                    paid_until = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
                
                # Get domain name
                domain_name_input = input(f'Enter domain name (e.g., "{schema_name}.localhost"): ').strip()
                if not domain_name_input:
                    self.stdout.write(self.style.ERROR('Domain name cannot be empty.'))
                    continue
                
                # Check if domain already exists
                if HotelDomain.objects.filter(domain=domain_name_input).exists():
                    self.stdout.write(self.style.ERROR(f'Domain "{domain_name_input}" already exists.'))
                    continue

                # Create tenant
                try:
                    tenant = HotelTenant.objects.create(
                        schema_name=schema_name,
                        name=tenant_name,
                        paid_until=paid_until,
                    )
                    self.stdout.write(self.style.SUCCESS(f'✅ Created tenant: {tenant.name}'))
                    
                    # Create domain
                    domain = HotelDomain.objects.create(
                        domain=domain_name_input,
                        tenant=tenant,
                        is_primary=True,
                    )
                    self.stdout.write(self.style.SUCCESS(f'✅ Created domain: {domain.domain}'))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error creating tenant: {e}'))
                    continue

                # Ask if they want to create another
                another = input('\nCreate another tenant? (yes/no): ').strip().lower()
                if another not in ['yes', 'y']:
                    break

        # ==========================================
        # 4. Summary
        # ==========================================
        self.stdout.write(self.style.NOTICE('\n' + '='*50))
        self.stdout.write(self.style.NOTICE('Tenant Summary'))
        self.stdout.write(self.style.NOTICE('='*50))
        
        tenants = HotelTenant.objects.all()
        for tenant in tenants:
            domains = HotelDomain.objects.filter(tenant=tenant)
            self.stdout.write(f'\n📦 {tenant.name}')
            self.stdout.write(f'   Schema: {tenant.schema_name}')
            self.stdout.write(f'   Domains: {", ".join([d.domain for d in domains])}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Setup complete! Total tenants: {tenants.count()}'))