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
class PaymentAttempt(models.Model):
    tenant = models.ForeignKey(HotelTenant, on_delete=models.CASCADE)
    table_number = models.IntegerField()
    seat = models.CharField(max_length=10)
    reference = models.CharField(max_length=20, unique=True)
    merchant_request_id = models.CharField(max_length=50, null=True, blank=True)
    checkout_request_id = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    cart_data = models.JSONField()   # store cart snapshot
    status = models.CharField(max_length=20, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'PaymentAttempt {self.reference} - {self.status}'
    class Meta:
        db_table = 'payment_attempts'

class SuperAdminProfile(models.Model):
    fName = models.CharField(max_length=50)
    lName = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    telephone = models.CharField(max_length=20)
    platformName = models.CharField(max_length=100)
    failed_attempt = models.IntegerField(default=0)
    is_blocked = models.BooleanField(default=False)

    def __str__(self):
        return self.email
    class Meta:
        db_table = 'super_admin_profiles'

class BlockedSuperAdmin(models.Model):
    email = models.EmailField(unique=True)
    blocked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    class Meta:
        db_table = 'blocked_super_admins'

class Bookings(models.Model):
    full_name = models.CharField(max_length=100)
    working_email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    tenant_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
        
