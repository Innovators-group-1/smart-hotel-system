from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from apps.platform_admin_flow.models import HotelTenant, HotelDomain

class Command(BaseCommand):
    help = 'Create a public schema for the platform admin'

    # Create the  platform admin
    def handle(self, *args, **options):
        # Platform Owner
        public_tenant, created = HotelTenant.objects.get_or_create(
            schema_name = 'public',
            defaults={
                'name': 'Platform Admin',
                'paid_until': '2025-12-31',
            }
        )
        public_domain, domain_created = HotelDomain.objects.get_or_create(
            domain = 'localhost',
            tenant = public_tenant,
            defaults = {
                'is_primary': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created Platform Admin tenant and domain'))
            
        if domain_created:
            self.stdout.write(self.style.SUCCESS('Successfully created Platform Admin domain'))
        
        if not created and not domain_created:
            self.stdout.write(self.style.WARNING('Platform Admin tenant and domain already exist'))
        

        # Creating tenants with interactive prompts and assigning domains to them
        while True:
            self.stdout.write(self.style.NOTICE("Creating a new tenant..."))

            schema_name = input('Enter schema name eg "calvidas_hotel" (or type "exit" to stop): ').strip()
            if schema_name.lower() == 'exit':
                break
            else:
                domain_exists = HotelDomain.objects.filter(tenant__schema_name=schema_name).exists()
                if domain_exists:
                    self.stdout.write(self.style.ERROR(f'Tenant with schema name "{schema_name}" already exists. Please choose a different name.'))
                    continue
            
            tenant_name = input('Enter tenant name eg "Calvidas Hotel": ').strip()
            if not tenant_name:
                self.stdout.write(self.style.ERROR('Tenant name cannot be empty. Please try again.'))
                continue
            paid_until = input('Enter paid until date (YYYY-MM-DD) eg "2024-12-31": ').strip()
            if not paid_until:
                self.stdout.write(self.style.ERROR('Paid until date cannot be empty. Please try again.'))
                continue
            domain_name = input('Enter domain name eg "calvidas.localhost": ').strip()
            if not domain_name:
                self.stdout.write(self.style.ERROR('Domain name cannot be empty. Please try again.'))
                continue
            another = input('Do you want to create another tenant? (yes/no): ').strip().lower()
            if another != 'yes':
                break

        # Create tenant
        tenant,created = HotelTenant.objects.get_or_create(
            schema_name = schema_name,
            defaults={
                'name': tenant_name,
                'paid_until': paid_until,
            }
        )
        tenant_domain, domain_created = HotelDomain.objects.get_or_create(
            domain = domain_name,
            tenant = tenant,
            defaults = {
                'is_primary': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created Calvidas Hotel tenant and domain'))
            # Manual creation of schemas using connection cursor
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {tenant.schema_name};')
                self.stdout.write(self.style.SUCCESS(f'Schema {tenant.schema_name} created successfully.'))
            # Migrate and create the tables on the for models in the common app
            call_command('migrate_schemas', schema_name=tenant.schema_name, app_label='common_flow', verbosity=0)
            
        if domain_created:
            self.stdout.write(self.style.SUCCESS('Successfully created Calvidas Hotel domain'))
            

        