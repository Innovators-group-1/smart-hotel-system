# --- Python Standard Library ---
import os
import random  
# --- Django Utilities ---
from django.utils.crypto import get_random_string  
from django.shortcuts import render, get_object_or_404, redirect 
from django.http import JsonResponse, HttpResponse 
import json
from django.db.models import Q 
from django.contrib import messages
import requests
from django.views.decorators.http import require_GET
# --- Third-Party Libraries ---

from .utils.payload import create_stk_push_payload  
from .utils.mpesa_utils import get_access_token, generate_password

# --- Local Application Models ---
from apps.common_flow.models import Menu as MenuItem, Category,MainCategory, Table, Order, OrderItem, HotelSettings
from apps.platform_admin_flow.models import PaymentIndex

def hotel_name_view(request):
    hotel_name = HotelSettings.objects.get_solo().hotel_name
    if not hotel_name:
        hotel_name = "Smart Hotel"
    return HttpResponse(hotel_name)
    
from django.db.models import Q

def menu_view(request, table_number):
    table = get_object_or_404(Table, number=table_number)
    request.session['table_number'] = table.number
    request.session.modified = True

    query = request.GET.get('q', '').strip()
    main_id = request.GET.get('main')       # main category id
    sub_id = request.GET.get('sub')         # subcategory id

    main_categories = MainCategory.objects.all()
    selected_main = None
    selected_sub = None
    menu_items = MenuItem.objects.filter(is_available=True)

    # Default to first main category if none selected
    if not main_id and main_categories.exists():
        selected_main = main_categories.first()
        subcategories = selected_main.categories.all()
        menu_items = menu_items.filter(category__main_category=selected_main)
    elif main_id:
        selected_main = get_object_or_404(MainCategory, main_category_id=main_id)
        subcategories = selected_main.categories.all()
        menu_items = menu_items.filter(category__main_category=selected_main)
    else:
        subcategories = Category.objects.none()

    # If user clicked a subcategory
    if sub_id:
        selected_sub = get_object_or_404(Category, category_id=sub_id)
        menu_items = menu_items.filter(category=selected_sub)

    # If user searched something
    if query:
        menu_items = menu_items.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    context = {
        "main_categories": main_categories,
        "sub_categories": subcategories,
        "menu_items": menu_items,
        "selected_main": selected_main.main_category_id if selected_main else None,
        "selected_sub": selected_sub.category_id if selected_sub else None,
        "query": query,
    }
    return render(request, "client_templates/menu/menu_page.html", context)


def menu_search_view(request):
    query = request.GET.get('q', '').strip()
    menu_items = MenuItem.objects.filter(is_available=True)

    if query:
        menu_items = menu_items.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    context = {'menu_items': menu_items}
    return render(request, 'client_templates/menu/partials/menu_list.html', context)

def menu_redirect_view(request):
    table_number = request.session.get('table_number')
    if table_number:
        return redirect('client_flow:menu', table_number=table_number)
    else:
        messages.error(request, "Table number not found in session. Please scan your table's QR code again.")
        return redirect('client_flow:menu', table_number=1)  

def _get_cart(session):
    return session.get('cart',{})

def _save_cart(session, cart):
    session['cart'] = cart
    session.modified = True

def add_to_cart(request, item_id):
    item = get_object_or_404(MenuItem, menu_item_id=item_id)
    cart = _get_cart(request.session)
    item_id_str = str(item_id)
    if item_id_str in cart:
        cart[item_id_str] += 1
    else:
        cart[item_id_str] = 1
    _save_cart(request.session, cart)

    cart_count = sum(cart.values())

    # Detect HTMX or AJAX requests
    is_htmx = request.headers.get('HX-Request') == 'true'
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    accepts_json = 'application/json' in request.headers.get('Accept', '')

    if is_htmx:
        # Return the added response to update the button and reset color of the button and prevent other clicks ie disable the button for good
        resp = HttpResponse(f'''<span class="text-green-600 font-medium">Added!</span>''')
        
        resp['HX-Trigger'] = json.dumps({'cartChanged': cart_count})
        return resp
    if is_ajax or accepts_json:
        resp = JsonResponse({'message': f'{item.title} added to cart.', 'cart_count': cart_count})
        resp['HX-Trigger'] = json.dumps({'cartChanged': cart_count})
        return resp

    messages.success(request, f'{item.title} added to cart.')
    return redirect('client_flow:menu_redirect')

@require_GET
def cart_count_view(request):
    cart = _get_cart(request.session)
    cart_count = sum(cart.values()) if cart else 0
    return JsonResponse({'cart_count': cart_count})

def update_cart(request, item_id):
    if request.method == "POST":
        cart = _get_cart(request.session)
        action = request.POST.get('action') or (request.headers.get('HX-Vals') and json.loads(request.headers.get('HX-Vals')).get('action'))
        item_id_str = str(item_id)
        if item_id_str not in cart:
            cart[item_id_str] = 0

        if action == 'increase':
            cart[item_id_str] += 1
        elif action == 'decrease':
            cart[item_id_str] -= 1
            if cart[item_id_str] <= 0:
                cart.pop(item_id_str, None)

        _save_cart(request.session, cart)

    # rebuild context
    cart = _get_cart(request.session)
    cart_items = []
    total = 0
    item_ids = [int(i) for i in cart.keys()] if cart else []
    items = MenuItem.objects.filter(menu_item_id__in=item_ids) if item_ids else []

    for item in items:
        qty = cart.get(str(item.menu_item_id), 0)
        subtotal = item.price * qty
        total += subtotal
        cart_items.append({"item": item, "quantity": qty, "subtotal": subtotal})

    resp = render(request, "client_templates/menu/partials/cart_container.html", {
        "cart_items": cart_items,
        "total": total,
    })
    resp['HX-Trigger'] = json.dumps({'cartChanged': sum(cart.values())})
    return resp


def remove_from_cart(request, item_id):
    cart = _get_cart(request.session)
    cart.pop(str(item_id), None)
    _save_cart(request.session, cart)

    # rebuild context (same as update_cart)
    cart_items = []
    total = 0
    item_ids = [int(i) for i in cart.keys()] if cart else []
    items = MenuItem.objects.filter(menu_item_id__in=item_ids) if item_ids else []

    for item in items:
        qty = cart.get(str(item.menu_item_id), 0)
        subtotal = item.price * qty
        total += subtotal
        cart_items.append({"item": item, "quantity": qty, "subtotal": subtotal})

    resp = render(request, "client_templates/menu/partials/cart_container.html", {
        "cart_items": cart_items,
        "total": total,
    })
    resp['HX-Trigger'] = json.dumps({'cartChanged': sum(cart.values())})
    return resp
def cart_view(request):
    cart = _get_cart(request.session)
    item_ids = [int(i) for i in cart.keys()]
    items = MenuItem.objects.filter(menu_item_id__in=item_ids)
    cart_items = []
    total = 0

    for item in items:
        quantity = cart[str(item.menu_item_id)]
        subtotal = item.price * quantity
        total += subtotal
        cart_items.append({'item': item, 'quantity': quantity, 'subtotal': subtotal})

    context = {'cart_items': cart_items, 'total': total}
    return render(request, 'client_templates/cart.html', context)
def seat_selector_view(request):
    table_number = request.session.get('table_number')
    table = get_object_or_404(Table, number=table_number)
    seat_range = range(1, table.seats + 1)

    return render(request, 'client_templates/menu/partials/seat_selector.html', {'table': table, 'seat_range': seat_range})

def set_seat_view(request):
    if request.method == 'POST':
        seat = request.POST.get('seat')
        request.session['seat'] = seat
        request.session.modified = True
        # Close the modal by returning an empty response
        return redirect('client_flow:checkout')

def checkout_view(request):
    # 1 Get cart from session
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('client_flow:menu_redirect')
    # 2 Retrieve MenuItem objects and calculate totals
    item_ids = [int(i) for i in cart.keys()]
    print(item_ids)
    items = MenuItem.objects.filter(menu_item_id__in=item_ids)
    cart_items = []
    total = 0

    for item in items:
        quantity = cart[str(item.menu_item_id)]
        subtotal = item.price * quantity
        total += subtotal
        cart_items.append({'item': item, 'quantity': quantity, 'subtotal': subtotal})

    # 3 Handle POST requests (when payment form is submitted)
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        table_number = request.session.get('table_number')
        seat = request.session.get('seat')

        try:
            table = get_object_or_404(Table,number=table_number)
        except Table.DoesNotExist:
            return HttpResponse('Table not found')

        if not table:
            messages.error(request, "No table available. Please add a table first.")
            return redirect('client_flow:menu')

        # EXPRESS PAYMENT
        if payment_method == 'express':
            
            account_number = request.POST.get('payment_account', '').strip()
            # Make the account number to start with country code if it doesn't and remove leading zeros
            if account_number and not account_number.startswith('254'):
                if account_number.startswith('0'):
                    account_number = '254' + account_number[1:]
                else:
                    account_number = '254' + account_number
            # Simulate sending payment request to gateway here
            payment_reference = f"EXP-{get_random_string(6).upper()}"  # Unique reference
            payment_method_value = Order.PaymentMethod.M_PESA

            # remove cents from the total amount for M-Pesa
            total = int(total)
            
        # CASH PAYMENT
        elif payment_method == 'cash':
            payment_reference = f"CASH-{get_random_string(6).upper()}"  # Unique code
            payment_method_value = Order.PaymentMethod.CASH

        else:
            messages.error(request, "Invalid payment method selected.")
            return redirect('client_flow:checkout')

        if not seat:
            messages.error(request, "Please select a seat before proceeding to checkout.")
            return redirect('client_flow:checkout')

        # Create the Order
        order = Order.objects.create(
            table=table,
            seat=seat,
            status=Order.OrderStatus.PENDING,
            payment_status=Order.PaymentStatus.UNPAID,
            payment_method=payment_method_value, 
            payment_number=request.POST.get('payment_account', ''),
            payment_reference=payment_reference,
            special_requests=request.POST.get('special_requests', ''),
        )

        # Create OrderItems
        for item in items:
            quantity = cart[str(item.pk)]
            subtotal = item.price * quantity

            OrderItem.objects.create(
                order=order,
                menu_item=item,
                quantity=quantity,
                total_price=subtotal,
            )

        print(f'this is the order that you have placed {order}')
        # simulate STK Push for M-Pesa payments
        if payment_method == 'express':
            # Create PaymentIndex record
            index_record = PaymentIndex.objects.create(
                tenant=request.tenant,
                order_ref=order.pk,
                account_reference=account_number,
            )
            # Simulate sending payment request to gateway here
            payload, headers = create_stk_push_payload(
                amount=total,
                phone_number=account_number,
                account_reference=payment_reference,
                transaction_desc="Hotel Order Payment"
            )
            # Send the STK Push request to M-Pesa
            response = requests.post(
                'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
                json=payload,
                headers=headers
            )
            if response.status_code == 200:
                response_data = response.json()
                # Update PaymentIndex with the checkout and merchant request IDs
                index_record.checkout_request_id = response_data.get('CheckoutRequestID')
                index_record.merchant_request_id = response_data.get('MerchantRequestID')
                index_record.save()
                print(f'STK Push initiated successfully: {response_data}')
            else:
                print(f'Failed to initiate STK Push: {response.text}')
            
        #  Clear cart
        request.session['cart'] = {}
        messages.success(request, f"Order confirmed! Payment reference: {payment_reference}")

        # Redirect to order confirmation with the order id
        return redirect('client_flow:order_confirmation', order_id=order.order_id)
        return HttpResponse('you have succcessfu;lly placed your order')

       

    # Render checkout page with cart items and total
    context = {'cart_items': cart_items, 'total': total}
    return render(request, 'client_templates/checkout.html', context)

def order_confirmation_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    # Get order items
    order_items = order.order_items.all()
    total_price = sum(item.total_price for item in order_items)
    return render(request, 'client_templates/order_confirmation.html', {
        'order': order,
        'order_items': order_items,
        'total_price': total_price
    })
    
def order_tracking_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    # Get related order items and totals for template display
    order_items = order.order_items.all()
    total_price = sum(item.total_price for item in order_items) if order_items else 0
    item_count = order_items.count()

    # Define all steps in the process (lowercase names used for internal matching)
    steps = ['pending', 'paid', 'confirmed', 'preparing', 'ready', 'served']

    # Robustly find current index: try matching order.status (lowercased),
    # fall back to payment_status or default to 0 if unknown.
    try:
        current_index = steps.index(order.status.lower())
    except Exception:
        try:
            current_index = steps.index(order.payment_status.lower())
        except Exception:
            current_index = 0

    # Build a list showing progress state
    progress = []
    for i, step in enumerate(steps):
        progress.append({
            'name': step.title(),
            'completed': i <= current_index,
            'active': i == current_index,
            'description': ''  # Will be set in template based on payment method
        })

    return render(request, 'client_templates/order_tracking.html', {
        'order': order,
        'order_items': order_items,
        'total_price': total_price,
        'item_count': item_count,
        'progress': progress
    })


def menu_filter_view(request, category_id):
    menu_items = MenuItem.objects.filter(category_id=category_id)
    context = {'menu_items': menu_items}

    return render(request, 'client_templates/menu/partials/menu_list.html', context)

def all_menu_items_view(request):
    menu_items = MenuItem.objects.all()
    context = {'menu_items': menu_items}

    return render(request, 'client_templates/menu/partials/menu_list.html', context)


def load_subcategories(request, main_id):
    """Return the subcategory navigation partial for a given main category.

    This view is used by HTMX when a main category button is clicked.
    """
    selected_main = get_object_or_404(MainCategory, main_category_id=main_id)
    subcategories = selected_main.categories.all()

    # Maintain the same context keys the partial expects
    context = {
        'sub_categories': subcategories,
        'selected_sub': None,
    }

    return render(request, 'client_templates/menu/partials/category_navi.html', context)


# views.py

def order_timeline_partial(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    
    # These are the 6 steps the user sees
    steps = [
        {'name': 'Pending', 'desc': 'Waiting for payment confirmation.'},
        {'name': 'Paid', 'desc': 'Payment received successfully.'},
        {'name': 'Confirmed', 'desc': 'Order confirmed by the team.'},
        {'name': 'Preparing', 'desc': 'Chef is preparing your meal.'},
        {'name': 'Ready', 'desc': 'Your order is ready to serve!'},
        {'name': 'Served', 'desc': 'Enjoy your meal!'}
    ]

    # Get the index (0-5) from your new model method
    current_step = order.get_tracking_step()

    progress_data = []
    for i, step in enumerate(steps):
        progress_data.append({
            'name': step['name'],
            'description': step['desc'],
            'completed': i <= current_step,
            'active': i == current_step
        })

    return render(request, 'client_templates/menu/partials/order_timeline.html', {
        'order': order,
        'progress': progress_data
    })
