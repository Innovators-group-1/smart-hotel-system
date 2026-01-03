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
    
class PaymentIndex(models.Model):
    tenant = models.ForeignKey(HotelTenant, on_delete=models.CASCADE)
    order_ref = models.CharField(max_length=100)
    account_reference = models.CharField(max_length=100 , null=True, blank=True)
    checkout_request_id = models.CharField(max_length=100 ,unique=True, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=100 , null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.name} | {self.order_ref} | {self.checkout_request_id or 'pending'}"
    class Meta:
        db_table = 'payment_index'
        indexes = [
            models.Index(fields=["order_ref"]),
            models.Index(fields=["account_reference"]),
            models.Index(fields=["checkout_request_id"]),
        ]

