from email.policy import default
from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
from PIL import Image, ImageDraw , ImageFont
from django.utils import timezone

from django.utils.text import slugify


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

# Main categories for menu items
class MainCategory(models.Model):
    main_category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, default='')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'main_category'

# Category model for categorizing items
class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    main_category = models.ForeignKey(MainCategory, on_delete=models.CASCADE, related_name='categories', default=None)
    slug = models.SlugField(unique=True, default='')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

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
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.title} ({self.category.name})'
    
    class Meta:
        db_table = 'menu'


class InbuiltMenuItems(models.Model):
    item_id = models.AutoField(primary_key=True)
    title = models.CharField( max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    picture = models.ImageField(upload_to='inbuilt_menus/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.title} ({self.category})'
    
    class Meta:
        db_table = 'inbuilt_menu_items'

class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)
    seats = models.PositiveIntegerField()
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
     
    # Overriding save method to generate QR code upon creating a new table
    def save(self, *args, **kwargs):
        #  Generate QR code that will redirect the customer to the menu page as well us identify the table uniquely
        qr_data = f'http://localhost:8000/client_flow/menu/{self.number}/'
        qr = qrcode.QRCode(
            version = 1,
            box_size = 10,
            border = 4
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color='darkgreen', back_color='white').convert('RGB')

        # Generate a qrcode with table number displayed below the QR code
        draw = ImageDraw.Draw(qr_img)
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=28)
        # Get hotel name from settings or use default
        settings = HotelSettings.objects.first()
        hotel_name = settings.hotel_name if settings and settings.hotel_name else "Smart Hotel"
        label = f' Scan to Order - Table {self.number}\n {hotel_name}'
        bbox = draw.textbbox((0,0), label, font=font, align='center')
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Create new canvas qrcode to fit both qr code and text
        canvas_height = qr_img.height + text_height + 40
        canvas = Image.new('RGB', (qr_img.width, canvas_height), 'white')
        canvas.paste(qr_img, (0,0))

        # draw text centered below the qr code
        text_x = (canvas.width - text_width) // 2
        text_y = qr_img.height + 10
        draw = ImageDraw.Draw(canvas)
        draw.multiline_text((text_x, text_y), label, fill='black', font=font, align='center')

        buffer = BytesIO()
        canvas.save(buffer, format='PNG')
        self.qr_code.save(f'table_{self.number}_qr.png', File(buffer), save=False)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Table {self.number} - Seats: {self.seats}'
    class Meta:
        db_table = 'table'

# Order Model to track customer orders
class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SENT_TO_KITCHEN = 'SENT_TO_KITCHEN', _('Sent to Kitchen')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
    
    class PaymentStatus(models.TextChoices):
        VERIFYING = 'VERIFYING', _('Verifying')
        UNPAID = 'UNPAID', _('Unpaid')
        PAID = 'PAID', _('Paid')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', _('Cash')
        M_PESA = 'M-PESA', _('M-PESA')
    
    order_id = models.AutoField(primary_key=True)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders')
    seat = models.PositiveIntegerField(null=False, blank=False)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    payment_number = models.CharField(max_length=50, blank=True, null=True)
    payment_reference = models.CharField(max_length=50, blank=True, null=True)
    # M-PESA specific fields
    mpesa_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    mpesa_receipt = models.CharField(max_length=50, blank=True, null=True)
    mpesa_phone = models.CharField(max_length=20, blank=True, null=True)
    mpesa_txn_date = models.DateTimeField(blank=True, null=True)
    mpesa_result_code = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    in_progress_period = models.DurationField(blank=True, null=True, default=timedelta(minutes=15))
    special_requests = models.TextField(blank=True, null=True)

    # Overriding save method to set completed_at timestamp when status changes
    def save(self, *args, **kwargs):
        if self.status == self.OrderStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now()

        if self.status == self.OrderStatus.IN_PROGRESS:
            self.in_progress_period = timezone.now() - self.created_at

        super().save(*args, **kwargs)

    # Represent Orders using Queue format FIFO
    class Meta:
        db_table = 'order'
        ordering = ['created_at']


class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1, null=True, blank=True)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, null=False, blank=False)

    def __str__(self):
        return f'{self.menu_item.title} x{self.quantity}'

    class Meta:
        db_table = 'order_items'


class Reports(models.Model):
    report_id = models.AutoField(primary_key=True)
    report_date = models.DateField(auto_now_add=True)
    total_orders = models.PositiveIntegerField()
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Report for {self.report_date} - Orders: {self.total_orders} - Revenue: {self.total_revenue}'
    
    class Meta:
        db_table = 'reports'
