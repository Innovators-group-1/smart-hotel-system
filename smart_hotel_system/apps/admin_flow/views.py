from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from apps.common_flow.models import HotelSettings,Reports,Order,Category,Menu,Table,InbuiltMenuItems,OrderItem
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
import json
from django.db.models import Sum,Value,DecimalField
from django.db.models.functions import TruncDay,Coalesce
from django.core.paginator import Paginator
from django.db import models


def is_htmx(request):
    """Robust detection for HTMX requests.

    Checks common headers Django/HTMX set. Returns True when the request
    originates from HTMX (so views can return partials).
    """
    try:
        # request.headers is case-insensitive mapping in recent Django
        hdr = request.headers.get('HX-Request', None)
        if hdr is None:
            hdr = request.headers.get('Hx-Request', None)
        if hdr is None:
            # WSGI may expose it in META as HTTP_HX_REQUEST
            hdr = request.META.get('HTTP_HX_REQUEST', None)
        if isinstance(hdr, str):
            return hdr.lower() == 'true'
        return False
    except Exception:
        return False

# Main admin dashboard view
def adminDashboard(request):
    hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'

    # Short order statistics
    completed_orders = Order.objects.filter(status='COMPLETED').count()
    pending_orders = Order.objects.filter(status='PENDING').count()
    cancelled_orders = Order.objects.filter(status='CANCELLED').count()
    in_progress_orders = Order.objects.filter(status='IN_PROGRESS').count()

    # Top five most ordered menu items
    top_meals = Menu.objects.annotate(order_count=Count('orders')).order_by('-order_count')[:5]

    # Recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    context = {
        'hotel_name': hotel_name,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'cancelled_orders': cancelled_orders,
        'in_progress_orders': in_progress_orders,
        'top_meals': top_meals,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_templates/dashboard.html', context)

# count orders views
def pending_orders_count(request):
    count = Order.objects.filter(status='PENDING').count()
    return HttpResponse(count)

def in_progress_orders_count(request):
    count = Order.objects.filter(status='IN_PROGRESS').count()
    return HttpResponse(count)
def completed_orders_count(request):
    count = Order.objects.filter(status='COMPLETED').count()
    return HttpResponse(count)
def cancelled_orders_count(request):
    count = Order.objects.filter(status='CANCELLED').count()
    return HttpResponse(count) 

# Partial views for different sections
# These views return HTML snippets for AJAX loading
# Example: orders_partial, menu_partial, reports_partial, settings_partial


def dashboard_partial(request):
    # Short order statistics
    completed_orders = Order.objects.filter(status='COMPLETED').count()
    pending_orders = Order.objects.filter(status='PENDING').count()
    cancelled_orders = Order.objects.filter(status='CANCELLED').count()
    in_progress_orders = Order.objects.filter(status='IN_PROGRESS').count()
    # Top five most ordered menu items
    top_meals = Menu.objects.annotate(order_count=Count('orders')).order_by('-order_count')[:5]

    # Recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    context = {
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'cancelled_orders': cancelled_orders,
        'in_progress_orders': in_progress_orders,
        'top_meals': top_meals,
        'recent_orders': recent_orders,
    }


    return render(request, 'admin_templates/partials/dashboard.html',context)
# Getting the Hotel Name
def get_hotel_name(request):
    hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'
    return HttpResponse(hotel_name)

def orders_partial(request):
    hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'
    orders = Order.objects.annotate(total=Sum('order_items__total_price')).all().order_by('-created_at')
    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(1)  # Default to page 1
    order_statuses = Order.OrderStatus.choices
    payment_statuses = Order.PaymentStatus.choices
    context = {'hotel_name': hotel_name, 'page_obj': page_obj, 'paginator': paginator, 'order_statuses': order_statuses, 'payment_statuses': payment_statuses}
    return render(request, 'admin_templates/partials/orders.html', context)

def menu_partial(request):
    hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'
    menu_items = Menu.objects.all()
    builtin_foods = InbuiltMenuItems.objects.all()
    categories = Category.objects.all()
    context = {
        'hotel_name': hotel_name,
        'menu_items': menu_items,
        'builtin_foods': builtin_foods,
        'categories': categories
    }
    return render(request, 'admin_templates/partials/menu.html', context)

# chats view for the admin dashboard
def sales_overview(request):
    sales = (Order.objects
        .filter(status='COMPLETED')
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total_sales=Coalesce(Sum('order_items__total_price'), Value(0),output_field=DecimalField(max_digits=10, decimal_places=2)))
        .order_by('day')
    )
    labels = [s["day"].strftime("%b %d") for s in sales]
    totals = [float(s["total_sales"]) for s in sales]

    context = {
        'labels': labels,
        'totals': totals,
    }
    html = render_to_string('admin_templates/partials/sales_overview_chart.html', context)
    return HttpResponse(html)




def reports_partial(request):
    hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'
    # Get total revenue and other metrics as needed
    # Fetching total revenue for last 7 days
    total_revenue = Order.objects.filter(
        status='COMPLETED',
        created_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).aggregate(
        total=Coalesce(Sum('order_items__total_price'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total']
    # Fetching avarage order value for last 7 days
    avarage_order_value = Order.objects.filter(
        status='COMPLETED',
        created_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).aggregate(
        average=Coalesce(Sum('order_items__total_price') / Count('order_id'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))
    )['average']
    # Fetching total orders for last 7 days
    totals_orders = Order.objects.filter(
        status='COMPLETED',
        created_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()
    # Fetching top Category with most orders
    category_sales = (
        OrderItem.objects
        .values("menu_item__category__name")
        .annotate(total_sales=Sum("total_price"))
        .order_by("-total_sales")
    )

    # Get the top category
    top_category = None
    if category_sales:
        top_category = category_sales[0]['menu_item__category__name']

    #aggregate orders by date
    orders_summary = (
        Order.objects
        .values("created_at__date")
        .annotate(
            total_orders=Count("order_id"),
            completed_orders=Count("order_id", filter=models.Q(status="COMPLETED")),
            cancelled_orders=Count("order_id", filter=models.Q(status="CANCELLED")),
            total_revenue=Sum("order_items__total_price"),
        )
        .order_by("-created_at__date")[:7]  # last 7 days
    )

    # Convert queryset into list of dicts with friendly keys
    summary_list = []
    for row in orders_summary:
        summary_list.append({
            "date": row["created_at__date"].strftime("%b %d, %Y"),
            "orders": row["total_orders"],
            "completed": row["completed_orders"],
            "cancelled": row["cancelled_orders"],
            "revenue": f"${row['total_revenue']:,.2f}" if row["total_revenue"] else "$0.00",
        })

    context = {
        'hotel_name': hotel_name,
        'total_revenue': total_revenue,
        'avarage_order_value': avarage_order_value,
        'totals_orders': totals_orders,
        'top_category': top_category,
        'orders_summary': summary_list,
    }
    return render(request, 'admin_templates/partials/reports.html', context)

def settings_partial(request):
    hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'
    context = {'hotel_name': hotel_name}
    return render(request, 'admin_templates/partials/settings.html', context)

def chefs_partial(request):
    hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'
    context = {'hotel_name': hotel_name}
    return render(request, 'admin_templates/partials/chefs.html', context)

def history_partial(request):
    hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'
    context = {'hotel_name': hotel_name}
    return render(request, 'admin_templates/partials/history.html', context)
# Settings partials views
def general_settings_partial(request):
    hotel_settings = HotelSettings.objects.first()
    context = {'hotel_settings': hotel_settings}
    return render(request, 'admin_templates/partials/setting-partials/general.html', context)

def display_settings_partial(request):
    return render(request, 'admin_templates/partials/setting-partials/display.html')

def table_settings_partial(request):
    tables = Table.objects.all()
    context = {'tables': tables}
    return render(request, 'admin_templates/partials/setting-partials/table.html', context)

def payment_settings_partial(request):
    return render(request, 'admin_templates/partials/setting-partials/payment.html')

def user_management_partial(request):
    return render(request, 'admin_templates/partials/setting-partials/user-management.html')

def notification_settings_partial(request):
    return render(request, 'admin_templates/partials/setting-partials/notifications.html')

def system_preferences_partial(request):
    return render(request, 'admin_templates/partials/setting-partials/system-preference.html')

def security_settings_partial(request):
    return render(request, 'admin_templates/partials/setting-partials/security.html')

def advanced_settings_partial(request):
    return render(request, 'admin_templates/partials/setting-partials/advanced.html')

# Settings form partial views
def update_general_settings(request):
    if request.method == 'POST':
        house_name = request.POST.get('name')
        address = request.POST.get('address')
        contact_email = request.POST.get('email')
        contact_phone = request.POST.get('phone')
        operating_hours = request.POST.get('hours')

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.hotel_name = house_name
        setting.address = address
        setting.contact_email = contact_email
        setting.contact_phone = contact_phone
        setting.operating_hours = operating_hours
        setting.save() 

        # Return the updated form partial to replace the form
        hotel_settings = HotelSettings.objects.first()
        context = {'hotel_settings': hotel_settings}
        return render(request, 'admin_templates/partials/setting-partials/general.html', context)

    return render(request, 'admin_templates/partials/setting-forms/general-settings-form.html')

def update_display_settings(request):
    if request.method == 'POST':
        theme = request.POST.get('theme')
        items_per_page = request.POST.get('items_per_page')

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.theme = theme
        setting.items_per_page = items_per_page
        setting.save() 

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "Display settings updated successfully."
                    }
                })
            }
        )
    
    return render(request, 'admin_templates/partials/setting-forms/display-settings-form.html')
# TABLE MANAGEMENT SETTINGS
def update_table_settings(request):
    if request.method == 'POST':
        auto_mark_available = request.POST.get('auto_mark_available') == 'on'
        auto_qr_generation = request.POST.get('auto_qr_generation') == 'on'
        table_section = request.POST.get('table_section')
        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.auto_mark_table_available = auto_mark_available
        setting.auto_qr_code_generation = auto_qr_generation
        setting.table_section = table_section
        setting.save() 

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "Table settings updated successfully."
                    }
                })
            }
        )

    return render(request, 'admin_templates/partials/setting-forms/table-settings-form.html')

def add_table(request):
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        seats = request.POST.get('seats')
        capacity = int(seats)

        # Create a new Table instance
        Table.objects.create(number=table_number, seats=capacity)

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "Table added successfully."
                    }
                })
            }
        )
    return render(request, 'admin_templates/partials/setting-forms/add-table-form.html')

def update_payment_settings(request):
    if request.method == 'POST':
        payment_gateway = request.POST.get('payment_gateway')
        currency = request.POST.get('currency')

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.payment_gateway = payment_gateway
        setting.currency = currency
        setting.save() 

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "Payment settings updated successfully."
                    }
                })
            }
        )
    return render(request, 'admin_templates/partials/setting-forms/payment-settings-form.html')

def update_user_management(request):   
    if request.method == 'POST':
            user_role = request.POST.get('user_role')
            access_level = request.POST.get('access_level')

            setting, created = HotelSettings.objects.get_or_create(id=1)
            setting.user_role = user_role
            setting.access_level = access_level
            setting.save() 

            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps({
                        "toast-success": {
                            "message": "User management settings updated successfully."
                        }
                    })
                }
            )
    return render(request, 'admin_templates/partials/setting-forms/user-management-form.html')

def update_notification_settings(request):
    if request.method == 'POST':
        email_notifications = request.POST.get('email_notifications') == 'on'
        sms_notifications = request.POST.get('sms_notifications') == 'on'

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.email_notifications = email_notifications
        setting.sms_notifications = sms_notifications
        setting.save() 

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "Notification settings updated successfully."
                    }
                })
            }
        )
    return render(request, 'admin_templates/partials/setting-forms/notification-settings-form.html')

def update_system_preferences(request):
    if request.method == 'POST':
        language = request.POST.get('language')
        timezone = request.POST.get('timezone')

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.language = language
        setting.timezone = timezone
        setting.save() 

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "System preferences updated successfully."
                    }
                })
            }
        )
    return render(request, 'admin_templates/partials/setting-forms/system-preferences-form.html')

def update_security_settings(request):
    if request.method == 'POST':
        two_factor_auth = request.POST.get('two_factor_auth') == 'on'
        password_expiry_days = request.POST.get('password_expiry_days')

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.two_factor_auth = two_factor_auth
        setting.password_expiry_days = password_expiry_days
        setting.save() 

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "Security settings updated successfully."
                    }
                })
            }
        )
    return render(request, 'admin_templates/partials/setting-forms/security-settings-form.html')

def update_advanced_settings(request):
    if request.method == 'POST':
        api_access = request.POST.get('api_access') == 'on'
        debug_mode = request.POST.get('debug_mode') == 'on'

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.api_access = api_access
        setting.debug_mode = debug_mode
        setting.save() 

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "Advanced settings updated successfully."
                    }
                })
            }
        )
    return render(request, 'admin_templates/partials/setting-forms/advanced-settings-form.html')

