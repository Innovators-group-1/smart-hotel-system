from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from django.template.loader import render_to_string
from apps.common_flow.models import Order
from django.db.models import Sum
from django.db.models import Q
from django.shortcuts import get_object_or_404
import json
from django.core.paginator import Paginator


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
        page_number = request.GET.get('page', 1)
        orders = Order.objects.annotate(order_total=Sum('order_items__total_price')).filter(
            Q(table__number__icontains=query) |
            Q(order_items__menu_item__title__icontains=query) |
            Q(status__icontains=query)
        ).distinct().order_by('-created_at')
        paginator = Paginator(orders, 10)
        page_obj = paginator.get_page(page_number)

        if is_htmx(request):
            html = render_to_string('admin_templates/partials/order-partials/order_list_partial.html', {'page_obj': page_obj, 'paginator': paginator})
            return HttpResponse(html)
        else:
            return render(request, 'admin_templates/orders.html', {'page_obj': page_obj, 'paginator': paginator})
    except Exception as SearchError:
        return HttpResponse(f"An error occurred: {str(SearchError)}", status=500)
       
def orders_filter_by_status(request, status):
    try:
        page_number = request.GET.get('page', 1)
        if status in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            orders = Order.objects.annotate(order_total=Sum('order_items__total_price')).filter(status=status).order_by('-created_at')
        else:
            orders = Order.objects.annotate(order_total=Sum('order_items__total_price')).all().order_by('-created_at')
        paginator = Paginator(orders, 10)
        page_obj = paginator.get_page(page_number)
        if is_htmx(request):
            html = render_to_string('admin_templates/partials/order-partials/order_list_partial.html', {'page_obj': page_obj, 'paginator': paginator})
            return HttpResponse(html)
        else:
            return render(request, 'admin_templates/orders.html', {'page_obj': page_obj, 'paginator': paginator})
    except Exception as FilterError:
        return HttpResponse(f"An error occurred: {str(FilterError)}", status=500)
    
def payment_status_filter(request, slug):
    try:
        page_number = request.GET.get('page', 1)
        if slug in ['PAID', 'UNPAID']:
            orders = Order.objects.annotate(order_total=Sum('order_items__total_price')).filter(payment_status=slug).order_by('-created_at')
        else:
            orders = Order.objects.annotate(order_total=Sum('order_items__total_price')).all().order_by('-created_at')
        paginator = Paginator(orders, 10)
        page_obj = paginator.get_page(page_number)
        if is_htmx(request):
            html = render_to_string('admin_templates/partials/order-partials/order_list_partial.html', {'page_obj': page_obj, 'paginator': paginator})
            return HttpResponse(html)
        else:
            return render(request, 'admin_templates/orders.html', {'page_obj': page_obj, 'paginator': paginator})
    except Exception as PaymentFilterError:
        return HttpResponse(f"An error occurred: {str(PaymentFilterError)}", status=500)

def order_list_partial(request):
    try:
        page_number = request.GET.get('page', 1)
        orders = Order.objects.annotate(order_total=Sum('order_items__total_price')).all().order_by('-created_at')
        paginator = Paginator(orders, 10)  # 10 orders per page
        page_obj = paginator.get_page(page_number)
        html = render_to_string('admin_templates/partials/order-partials/order_list_partial.html', {'page_obj': page_obj, 'paginator': paginator})
        return HttpResponse(html)
    except Exception as PartialError:
        return HttpResponse(f"An error occurred: {str(PartialError)}", status=500)
    
def order_row_partial(request,order_id):
    try:
        order = get_object_or_404(Order, pk=order_id)
        total = sum(item.total_price for item in order.order_items.all())
        html = render_to_string('admin_templates/partials/order-partials/order_row_partial.html',{'order':order, 'total': total})
        return HttpResponse(html)
    except Exception as OrderRowError:
        return HttpResponse(f"An error occurred: {str(OrderRowError)}", status=500)

def order_details_partial(request, order_id):
    try:
        order = get_object_or_404(Order.objects.prefetch_related('order_items__menu_item', 'table'), pk=order_id)
        total = sum(item.total_price for item in order.order_items.all())
        html = render_to_string('admin_templates/partials/order-partials/order_details_partial.html', {'order': order, 'total': total})
        return HttpResponse(html)
    except Exception as DetailsError:
        return HttpResponse(f"An error occurred: {str(DetailsError)}", status=500)

def orders_page(request, page_number):
    try:
        orders = Order.objects.annotate(order_total=Sum('order_items__total_price')).all().order_by('-created_at')
        paginator = Paginator(orders, 10)
        page_obj = paginator.get_page(page_number)
        html = render_to_string('admin_templates/partials/order-partials/order_list_partial.html', {'page_obj': page_obj, 'paginator': paginator})
        return HttpResponse(html)
    except Exception as PageError:
        return HttpResponse(f"An error occurred: {str(PageError)}", status=500)

def verify_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.payment_method == Order.PaymentMethod.CASH:
        if order.payment_status != Order.PaymentStatus.PAID:
            order.payment_status = Order.PaymentStatus.PAID
            # Automatically send to kitchen when payment is verified
            order.status = Order.OrderStatus.SENT_TO_KITCHEN
            order.save(update_fields=['payment_status', 'status'])
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps({
                        "toast-success": {
                            "message": "Cash payment verified and order sent to kitchen."
                        }
                    })
                }
            )
        else:
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps({
                        "toast-error": {
                            "message": "Payment already processed."
                        }
                    })
                }
            )
    else:
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-error": {
                        "message": "An Error occurred during CASH verification."
                    }
                })
            }
        )

def mpesa_verification_partial(request, order_id):
    try:
        order = get_object_or_404(Order, pk=order_id)
        html = render_to_string('admin_templates/partials/order-partials/mpesa_verify.html', {'order': order})
        return HttpResponse(html)
    except Exception as MpesaPartialError:
        return HttpResponse(f"An error occurred: {str(MpesaPartialError)}", status=500)

def confirm_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.payment_method == Order.PaymentMethod.M_PESA:
        if order.payment_status != Order.PaymentStatus.PAID:
            order.payment_status = Order.PaymentStatus.PAID
            # Automatically send to kitchen when payment is verified
            order.status = Order.OrderStatus.SENT_TO_KITCHEN
            order.save(update_fields=['payment_status', 'status'])
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps({
                        "toast-success": {
                            "message": "M-Pesa payment confirmed and order sent to kitchen."
                        }
                    })
                }
            )
        else:
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps({
                        "toast-error": {
                            "message": "Payment already processed."
                        }
                    })
                }
            )
    else:
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-error": {
                        "message": "An Error occurred during M-Pesa confirmation."
                    }
                })
            }
        )

def mark_unpaid(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.payment_status != Order.PaymentStatus.UNPAID:
        order.payment_status = Order.PaymentStatus.UNPAID
        order.save(update_fields=['payment_status'])
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "Order marked as unpaid."
                    }
                })
            }
        )
    else:
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-error": {
                        "message": "Order is already marked as unpaid."
                    }
                })
            }
        )

def send_to_kitchen(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order:
        # check if the order payment status is PAID before sending to kitchen
        if order.payment_status != Order.PaymentStatus.PAID:
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps({
                        "toast-error": {
                            "message": "Cannot send to kitchen. Payment not verified."
                        }
                    })
                }
            )
        # Check if order is already sent to kitchen
        if order.status == Order.OrderStatus.SENT_TO_KITCHEN:
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps({
                        "toast-error": {
                            "message": "Order is already sent to kitchen."
                        }
                    })
                }
            )
        order.status = Order.OrderStatus.SENT_TO_KITCHEN
        order.save(update_fields=['status'])
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "Order sent to kitchen successfully."
                    }
                })
            }
        )
    

def print_receipt(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    # Here you could generate a PDF or something, but for now just show success
    return HttpResponse(
        status=204,
        headers={
            "HX-Trigger": json.dumps({
                "toast-success": {
                    "message": "Receipt printed successfully."
                }
            })
        }
    )

def cancel_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.status != Order.OrderStatus.CANCELLED:
        order.status = Order.OrderStatus.CANCELLED
        order.save(update_fields=['status'])
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-success": {
                        "message": "Order cancelled successfully."
                    }
                })
            }
        )
    else:
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "toast-error": {
                        "message": "Order is already cancelled."
                    }
                })
            }
        )

