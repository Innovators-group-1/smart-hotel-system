from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from django.template.loader import render_to_string
from apps.common_flow.models import Orders
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
import json


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
    

# Additional order management views would go here
def orders_search(request):
    try:
        query = request.GET.get('q', '')
        orders = Orders.objects.filter(
            Q(table__number__icontains=query) |
            Q(menu_item__title__icontains=query) |
            Q(status__icontains=query)
        ).order_by('-created_at')

        if is_htmx(request):
            html = render_to_string('admin_templates/partials/order_list_partial.html', {'orders': orders})
            return HttpResponse(html)
        else:
            return render(request, 'admin_templates/orders.html', {'orders': orders})
    except Exception as SearchError:
        return HttpResponse(f"An error occurred: {str(SearchError)}", status=500)
       
def orders_filter_by_status(request, status):
    try:
        if status in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            orders = Orders.objects.filter(status=status).order_by('-created_at')
        else:
            orders = Orders.objects.all().order_by('-created_at')
        if is_htmx(request):
            html = render_to_string('admin_templates/partials/order_list_partial.html', {'orders': orders})
            return HttpResponse(html)
        else:
            return render(request, 'admin_templates/orders.html', {'orders': orders})
    except Exception as FilterError:
        return HttpResponse(f"An error occurred: {str(FilterError)}", status=500)
    
def payment_status_filter(request, slug):
    try:
        if slug in ['PAID', 'UNPAID']:
            orders = Orders.objects.filter(payment_status=slug).order_by('-created_at')
        else:
            orders = Orders.objects.all().order_by('-created_at')
        if is_htmx(request):
            html = render_to_string('admin_templates/partials/order_list_partial.html', {'orders': orders})
            return HttpResponse(html)
        else:
            return render(request, 'admin_templates/orders.html', {'orders': orders})
    except Exception as PaymentFilterError:
        return HttpResponse(f"An error occurred: {str(PaymentFilterError)}", status=500)

def order_list_partial(request):
    try:
        orders = Orders.objects.all().order_by('-created_at')
        html = render_to_string('admin_templates/partials/order_list_partial.html', {'orders': orders})
        return HttpResponse(html)
    except Exception as PartialError:
        return HttpResponse(f"An error occurred: {str(PartialError)}", status=500)

def order_details_partial(request, order_id):
    try:
        order = get_object_or_404(Orders, pk=order_id)
        html = render_to_string('admin_templates/partials/order_details_partial.html', {'order': order})
        return HttpResponse(html)
    except Exception as DetailsError:
        return HttpResponse(f"An error occurred: {str(DetailsError)}", status=500)

def orders_page(request, page_number):
    HttpResponse("Paging functionality to be implemented.")

def verify_payment(request, order_id):
    HttpResponse("Payment verification functionality to be implemented.")
def send_to_kitchen(request, order_id):
    HttpResponse("Send to kitchen functionality to be implemented.")
def print_receipt(request, order_id):
    HttpResponse("Print receipt functionality to be implemented.")
def cancel_order(request, order_id):
    HttpResponse("Cancel order functionality to be implemented.")

