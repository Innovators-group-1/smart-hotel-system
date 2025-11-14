from django.contrib import admin
from .models import HotelTenant, HotelDomain

# Register your models here.
@admin.register(HotelTenant)
class HotelTenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'paid_until', 'on_trial', 'created_on')

@admin.register(HotelDomain)
class HotelDomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
