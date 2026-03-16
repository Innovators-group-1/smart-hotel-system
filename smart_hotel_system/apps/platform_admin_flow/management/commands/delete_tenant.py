from django.core.management.base import BaseCommand
from django.db import connection
from apps.platform_admin_flow.models import HotelTenant, HotelDomain

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('schema_name', type=str)

    def handle(self, *args, **options):
        schema = options['schema_name']
        HotelDomain.objects.filter(tenant__schema_name=schema).delete()
        HotelTenant.objects.filter(schema_name=schema).delete()
        with connection.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        self.stdout.write(f'✅ Deleted tenant: {schema}')