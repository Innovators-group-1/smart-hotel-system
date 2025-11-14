from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

# My tenant model that extends TenantMixin
class HotelTenant(TenantMixin):
    name = models.CharField(max_length=100)
    paid_until = models.DateField()
    on_trial = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = False
    # default true, schema will be automatically dropped when it is deleted
    auto_drop_schema = True

    def __str__(self):
        return self.name
# My domain model that extends DomainMixin

class HotelDomain(DomainMixin):
    pass
    def __str__(self):
        return self.domain
    

