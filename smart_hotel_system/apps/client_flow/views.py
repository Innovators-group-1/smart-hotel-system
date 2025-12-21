# --- Python Standard Library ---
import random  # Used for generating random cash payment codes

# --- Django Utilities ---
from django.utils.crypto import get_random_string  
from django.shortcuts import render, get_object_or_404, redirect 
from django.http import JsonResponse, HttpResponse 
import json
from django.db.models import Q 
from django.contrib import messages  

# --- Local Application Models ---
from apps.common_flow.models import Menu as MenuItem, Category, Table,Orders,HotelSettings

def hotel_name_view(request):
    hotel_name = HotelSettings.objects.get_solo().hotel_name
    if not hotel_name:
        hotel_name = "Smart Hotel"
    return HttpResponse(hotel_name)
    


def _get_cart(session):
    return session.get('cart',{})

def _save_cart(session, cart):
    session['cart'] = cart
    session.modified = True

def add_to_cart(request, item_id):
    item = get_object_or_404(MenuItem, menu_item_id=item_id)
    cart = _get_cart(request.session)
    print(cart)
    item_id_str = str(item_id)
    if item_id_str in cart:
        cart[item_id_str] += 1
    else:
        cart[item_id_str] = 1
    _save_cart(request.session, cart)

    # Prepare response data
    cart_count = sum(cart.values())
    data = {'message': f'{item.title} added to cart.', 'cart_count': cart_count}

    # Detect HTMX or AJAX requests and return JSON so the page isn't redirected/refreshed.
    is_htmx = request.headers.get('HX-Request') == 'true'
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    accepts_json = 'application/json' in request.headers.get('Accept', '')

    if is_htmx or is_ajax or accepts_json:
        # For HTMX: return no body but trigger a client event with the new cart count
        # so the frontend can update the cart count without parsing JSON.
        headers = {
            'HX-Trigger': json.dumps({'cartChanged': cart_count})
        }
        # 204 No Content is appropriate since we don't send a JSON body
        return HttpResponse(status=204, headers=headers)

    # Fallback for regular (non-AJAX) requests: keep previous behavior
    messages.success(request, data['message'])
    return redirect('client_flow:menu')

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

def update_cart(request, item_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        cart = _get_cart(request.session)

        if str(item_id) in cart:
            if action == 'increase':
                cart[str(item_id)] += 1
                messages.success(request, 'Cart updated successfully.')
            elif action == 'decrease':
                if cart[str(item_id)] > 1:
                    cart[str(item_id)] -= 1
                    messages.success(request, 'Cart updated successfully.')
                else:
                    del cart[str(item_id)]
                    messages.success(request, 'Item removed from cart.')

            _save_cart(request.session, cart)
        return redirect('client_flow:cart')

def remove_from_cart(request, item_id):
    cart = _get_cart(request.session)
    if str(item_id) in cart:
        del cart[str(item_id)]
        _save_cart(request.session, cart)
        messages.info(request, "Item removed from cart.")
    return redirect('client_flow:cart')

def checkout_view(request):
    # 1 Get cart from session
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('client_flow:menu')

    # 2 Retrieve MenuItem objects and calculate totals
    item_ids = [int(i) for i in cart.keys()]
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
        table = Table.objects.first()  # For now, pick the first table. Replace as needed.

        if not table:
            messages.error(request, "No table available. Please add a table first.")
            return redirect('client_flow:menu')

        # EXPRESS PAYMENT
        if payment_method == 'express':
            account_number = request.POST.get('payment_account', '').strip()
            if not account_number:
                messages.error(request, "Please enter a phone or account number for express payment.")
                return redirect('client_flow:checkout')

            # Simulate sending payment request to gateway here
            payment_reference = f"EXP-{get_random_string(6).upper()}"  # Unique reference

        # CASH PAYMENT
        elif payment_method == 'cash':
            payment_reference = f"CASH-{get_random_string(6).upper()}"  # Unique code

        else:
            messages.error(request, "Invalid payment method selected.")
            return redirect('client_flow:checkout')

        #  Create Order
        order = Orders.objects.create(
            table=table,
            payment_method=payment_method,
            payment_reference=payment_reference,
            status='pending',
            total_amount=total
        )

        #  Create OrderItems
        # for row in cart_items:
        #     OrderItem.objects.create(
        #         order=order,
        #         menu_item=row['item'],
        #         quantity=row['quantity'],
        #         unit_price=row['item'].price
        #     )

        #  Clear cart
        request.session['cart'] = {}
        messages.success(request, f"Order confirmed! Payment reference: {payment_reference}")

        #  Redirect to order confirmation page or menu
        return redirect('client_flow:order_confirmation', order_id=order.id)

    # Render checkout page with cart items and total
    context = {'cart_items': cart_items, 'total': total}
    return render(request, 'client_templates/checkout.html', context)

def order_confirmation_view(request, order_id):
    order = get_object_or_404(Orders, id=order_id)
    order_items = order.order_items.all()
    return render(request, 'client_templates/order_confirmation.html', {
        'order': order,
        'order_items': order_items
    })
    
def order_tracking_view(request, order_id):
    order = get_object_or_404(Orders, id=order_id)

    # Define all steps in the process
    steps = ['pending', 'paid', 'confirmed', 'preparing', 'ready', 'served']
    current_index = steps.index(order.status)

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
        'progress': progress
    }) 


def menu_view(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')  # Get selected category from URL

    categories = Category.objects.all()
    selected_category = None
    menu_items = MenuItem.objects.filter(is_available=True)

    # If user clicked a category
    if category_id:
        selected_category = get_object_or_404(Category, id=category_id)
        menu_items = menu_items.filter(category=selected_category)

    # If user searched something
    if query:
        menu_items = menu_items.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    context = {
        'categories': categories,
        'menu_items': menu_items,
        'selected_category': selected_category.id if selected_category else None,
        'query': query,
    }

    return render(request, 'client_templates/menu/menu_page.html', context)

def menu_filter_view(request, category_id):
    menu_items = MenuItem.objects.filter(category_id=category_id)
    context = {'menu_items': menu_items}

    return render(request, 'client_templates/menu/partials/menu_list.html', context)

def all_menu_items_view(request):
    menu_items = MenuItem.objects.all()
    context = {'menu_items': menu_items}

    return render(request, 'client_templates/menu/partials/menu_list.html', context)
