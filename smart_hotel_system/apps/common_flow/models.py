from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta


# Common model to be used across different apps
class HotelSettings(models.Model):
    # Define various settings fields
    # general hotel settings
    hotel_name = models.CharField(max_length=200)
    address = models.TextField()
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    timezone = models.CharField(max_length=50, default='UTC')
    # operational preferences
    operating_hours = models.CharField(max_length=100, default='09:00 - 22:00')

    # Table settings
    auto_mark_table_available = models.BooleanField(default=True)
    auto_qr_code_generation = models.BooleanField(default=True)
    table_section = models.CharField(max_length=100, default='Indoor')
    # display preferences
    menu_display_style = models.CharField(max_length=50, default='grid')
    menu_theme_color = models.CharField(max_length=7, default='#FFFFFF')
   

    class Meta:
        db_table = 'hotel_settings'

# Category model for categorizing items
class Category(models.Model):
    Category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'category' 
    
    
class Menu (models.Model):
    menu_item_id = models.AutoField(primary_key=True)
    title = models.CharField( max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    picture = models.ImageField(upload_to='menus/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='menus')

    def __str__(self):
        return f'{self.title} ({self.category.name})'
    
    class Meta:
        db_table = 'menu'

class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)
    seats = models.PositiveIntegerField()
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
     
    # Overriding save method to generate QR code upon creating a new table
    def save(self, *args, **kwargs):
        #  Generate QR code that will redirect the customer to the menu page as well us identify the table uniquely
        qr_data = f'http://localhost:8000/menu/?table={self.number}'
        qr_code_img = qrcode.make(qr_data)
        buffer = BytesIO()
        qr_code_img.save(buffer, format='PNG')
        self.qr_code.save(f'table_{self.number}_qrcode.png', File(buffer), save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Table {self.number} - Seats: {self.seats}'
    class Meta:
        db_table = 'table'

# Order Model to track customer orders
class Orders(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
    order_id = models.AutoField(primary_key=True)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders')
    seat = models.PositiveIntegerField(null = False, blank = False)
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1,null=True, blank=True)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, null=False, blank=False)
    status = models.CharField(max_length = 20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    in_progress_period = models.DurationField(blank=True, null=True, default=timedelta(minutes=15))
    special_requests = models.TextField(blank=True, null=True)

    # Overriding save method to set completed_at timestamp when status changes to COMPLETED and update in_progress_period
    def save(self, *args, **kwargs):

        if self.status == self.OrderStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now()
            super().save(*args, **kwargs)

        if self.status == self.OrderStatus.IN_PROGRESS:
            self.in_progress_period = datetime.now() - self.created_at
            super().save(*args, **kwargs)
    

    # Represent Orders using Queue format FIFO
    class Meta:
        db_table = 'orders'
        ordering = ['created_at']

    def __str__(self):
        return f'Order {self.id} - Table {self.table.number} - {self.menu_item.title} x{self.quantity} ({self.status})'
    
class Reports(models.Model):
    report_id = models.AutoField(primary_key=True)
    report_date = models.DateField(auto_now_add=True)
    total_orders = models.PositiveIntegerField()
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Report for {self.report_date} - Orders: {self.total_orders} - Revenue: {self.total_revenue}'
    
    class Meta:
        db_table = 'reports'

