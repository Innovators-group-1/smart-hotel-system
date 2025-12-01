from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from apps.common_flow.models import HotelSettings,Reports,Orders,Category,Menu,Table,InbuiltMenuItems
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

# Main admin dashboard view
def adminDashboard(request):
    hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'

    # Short order statistics
    completed_orders = Orders.objects.filter(status='COMPLETED').count()
    pending_orders = Orders.objects.filter(status='PENDING').count()
    cancelled_orders = Orders.objects.filter(status='CANCELLED').count()
    in_progress_orders = Orders.objects.filter(status='IN_PROGRESS').count()

    # Top five most ordered menu items
    top_meals = Menu.objects.annotate(order_count=Count('orders')).order_by('-order_count')[:5]

    # Recent orders
    recent_orders = Orders.objects.all().order_by('-created_at')[:5]

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

# Partial views for different sections
# These views return HTML snippets for AJAX loading
# Example: orders_partial, menu_partial, reports_partial, settings_partial


def dashboard_partial(request):
    # Short order statistics
    completed_orders = Orders.objects.filter(status='completed').count()
    pending_orders = Orders.objects.filter(status='pending').count()
    cancelled_orders = Orders.objects.filter(status='cancelled').count()
    in_progress_orders = Orders.objects.filter(status='in_progress').count()

    # Top five most ordered menu items
    top_meals = Menu.objects.annotate(order_count=Count('orders')).order_by('-order_count')[:5]

    # Recent orders
    recent_orders = Orders.objects.all().order_by('-created_at')[:5]

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
    orders = Orders.objects.all().order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'admin_templates/partials/orders.html', context)

def menu_partial(request):
    menu_items = Menu.objects.all()
    builtin_foods = InbuiltMenuItems.objects.all()
    categories = Category.objects.all()
    context = {
        'menu_items': menu_items,
        'builtin_foods': builtin_foods,
        'categories': categories
    }
    return render(request, 'admin_templates/partials/menu.html', context)

def reports_partial(request):
    reports = Reports.objects.all().order_by('-date_generated')
    context = {'reports': reports}
    return render(request, 'admin_templates/partials/reports.html', context)

def settings_partial(request):
    return render(request, 'admin_templates/partials/settings.html')

def chefs_partial(request):
    return render(request, 'admin_templates/partials/chefs.html')

def history_partial(request):
    return render(request, 'admin_templates/partials/history.html')

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

        return JsonResponse({'status': 'success', 'message': 'Display settings updated successfully.'})
    
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

        return JsonResponse({'status': 'success', 'message': 'Table settings updated successfully.'})

    return render(request, 'admin_templates/partials/setting-forms/table-settings-form.html')

def add_table(request):
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        seats = request.POST.get('seats')
        capacity = int(seats)

        # Create a new Table instance
        Table.objects.create(number=table_number, seats=capacity)

        return JsonResponse({'status': 'success', 'message': 'Table added successfully.'})
    return render(request, 'admin_templates/partials/setting-forms/add-table-form.html')

def update_payment_settings(request):
    if request.method == 'POST':
        payment_gateway = request.POST.get('payment_gateway')
        currency = request.POST.get('currency')

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.payment_gateway = payment_gateway
        setting.currency = currency
        setting.save() 

        return JsonResponse({'status': 'success', 'message': 'Payment settings updated successfully.'})
    return render(request, 'admin_templates/partials/setting-forms/payment-settings-form.html')

def update_user_management(request):   
    if request.method == 'POST':
            user_role = request.POST.get('user_role')
            access_level = request.POST.get('access_level')

            setting, created = HotelSettings.objects.get_or_create(id=1)
            setting.user_role = user_role
            setting.access_level = access_level
            setting.save() 

            return JsonResponse({'status': 'success', 'message': 'User management settings updated successfully.'})   
    return render(request, 'admin_templates/partials/setting-forms/user-management-form.html')

def update_notification_settings(request):
    if request.method == 'POST':
        email_notifications = request.POST.get('email_notifications') == 'on'
        sms_notifications = request.POST.get('sms_notifications') == 'on'

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.email_notifications = email_notifications
        setting.sms_notifications = sms_notifications
        setting.save() 

        return JsonResponse({'status': 'success', 'message': 'Notification settings updated successfully.'})
    return render(request, 'admin_templates/partials/setting-forms/notification-settings-form.html')

def update_system_preferences(request):
    if request.method == 'POST':
        language = request.POST.get('language')
        timezone = request.POST.get('timezone')

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.language = language
        setting.timezone = timezone
        setting.save() 

        return JsonResponse({'status': 'success', 'message': 'System preferences updated successfully.'})
    return render(request, 'admin_templates/partials/setting-forms/system-preferences-form.html')

def update_security_settings(request):
    if request.method == 'POST':
        two_factor_auth = request.POST.get('two_factor_auth') == 'on'
        password_expiry_days = request.POST.get('password_expiry_days')

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.two_factor_auth = two_factor_auth
        setting.password_expiry_days = password_expiry_days
        setting.save() 

        return JsonResponse({'status': 'success', 'message': 'Security settings updated successfully.'})
    return render(request, 'admin_templates/partials/setting-forms/security-settings-form.html')

def update_advanced_settings(request):
    if request.method == 'POST':
        api_access = request.POST.get('api_access') == 'on'
        debug_mode = request.POST.get('debug_mode') == 'on'

        setting, created = HotelSettings.objects.get_or_create(id=1)
        setting.api_access = api_access
        setting.debug_mode = debug_mode
        setting.save() 

        return JsonResponse({'status': 'success', 'message': 'Advanced settings updated successfully.'})
    return render(request, 'admin_templates/partials/setting-forms/advanced-settings-form.html')


# MENU MANAGEMENT VIEWS
def add_menu_item(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        category_id = request.POST.get('category')
        category = Category.objects.get(pk=category_id) if category_id else None

        Menu.objects.create(
            title=name,
            description=description,
            price=price,
            picture=image,
            category=category
        )

        return JsonResponse({'status': 'success', 'message': 'Menu item added successfully.'})
    
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'admin_templates/partials/menu-forms/add-menu-item-form.html', context)


def add_inbuilt_menu_item(request,id):
    if request.method == "POST":
        inbuilt_item = InbuiltMenuItems.objects.get(item_id=id)

        Menu.objects.create(
            title = inbuilt_item.title,
            description = inbuilt_item.description,
            price = inbuilt_item.price,
            picture = inbuilt_item.picture,
            category = inbuilt_item.category
        )

        return JsonResponse({'status': 'success', 'message': 'Menu item added successfully.'})
    return render(request,'admin_templates/partials/menu-forms/add-menu-item-form.html')

def tap_add_inbuilt_menu_item(request,item_id):
    if request.method != "POST":
      return HttpResponse("Invalid request method.")
    inbuilt_item = get_object_or_404(InbuiltMenuItems, item_id=item_id)

    #    prevent duplication of items by adding same inbuilt item
    if Menu.objects.filter(title=inbuilt_item.title, description=inbuilt_item.description, price=inbuilt_item.price).exists():
       return JsonResponse({'status': 'error', 'message': 'This inbuilt menu item already exists in the menu.'})
    Menu.objects.create(
       title=inbuilt_item.title,
       description=inbuilt_item.description,
       price=inbuilt_item.price,
       picture=inbuilt_item.picture,
       category=inbuilt_item.category
    )
    # Query the menu row items again to update the menu list
    menu_items = Menu.objects.all().order_by('menu_item_id')
    context = {'menu_items': menu_items}
    
    # if it is htmx request return the updated menu rows partial
    if request.headers.get('Hx-Request') == 'true':
       return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)
    
    # Otherwise redirect to the menu partial
    return render(request, 'admin_templates/partials/menu.html', context)

def menu_search(request):
    query = request.GET.get('query','')
    menu_items = Menu.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
    context = {'menu_items': menu_items}
    return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)

def menu_filter(request,slug):
    category = get_object_or_404(Category, slug=slug)
    menu_items = Menu.objects.filter(category=category)
    context = {'menu_items': menu_items}
    return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)

def toggle_menu_availability(request, item_id):
    menu_item = get_object_or_404(Menu, menu_item_id = item_id)
    menu_item.is_available = not menu_item.is_available
    menu_item.save()

    menu_items = Menu.objects.all().order_by('menu_item_id')
    context = {'menu_items': menu_items}
    return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)

def edit_menu_item(request, item_id):
    menu_item = get_object_or_404(Menu, menu_item_id=item_id)

    if request.method == 'POST':
        menu_item.title = request.POST.get('name')
        menu_item.description = request.POST.get('description')
        menu_item.price = request.POST.get('price')
        image = request.FILES.get('image')
        if image:
            menu_item.picture = image
        category_id = request.POST.get('category')
        menu_item.category = Category.objects.get(pk=category_id) if category_id else None
        menu_item.save()

        return JsonResponse({'status': 'success', 'message': 'Menu item updated successfully.'})

    categories = Category.objects.all()
    context = {
        'menu_item': menu_item,
        'categories': categories
    }
    return render(request, 'admin_templates/partials/menu-forms/edit-menu-item-form.html', context)

def delete_menu_item(request, item_id):
    menu_item = get_object_or_404(Menu, menu_item_id=item_id)
    menu_item.delete()

    menu_items = Menu.objects.all().order_by('menu_item_id')
    context = {'menu_items': menu_items}
    return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)



