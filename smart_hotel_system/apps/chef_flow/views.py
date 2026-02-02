from django.shortcuts import render, get_object_or_404, redirect
from apps.common_flow.models import Order, HotelSettings
from django_tenants.utils import schema_context
from django.http import HttpResponse

def chef_dashboard(request):
    """
    Main dashboard view.
    Fetches all orders grouped by their kitchen status.
    """
    with schema_context(request.tenant.schema_name):
        hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'
        pending_orders = Order.objects.select_related("table").prefetch_related("order_items__menu_item").filter(
            status=Order.OrderStatus.SENT_TO_KITCHEN
        )
        active_orders = Order.objects.select_related("table").prefetch_related("order_items__menu_item").filter(
            status=Order.OrderStatus.IN_PROGRESS
        )

        completed_orders = Order.objects.select_related("table").prefetch_related("order_items__menu_item").filter(
            status=Order.OrderStatus.COMPLETED
        ).order_by("-completed_at")[:5]

        urgent_orders = Order.objects.select_related("table").prefetch_related("order_items__menu_item").filter(
            special_requests__isnull=False
        ).exclude(special_requests="").exclude(
            status=Order.OrderStatus.COMPLETED
        )

    context = {
        "pending_orders": pending_orders,
        "hotel_name": hotel_name,
        "active_orders": active_orders,
        "completed_orders": completed_orders,
        "urgent_orders": urgent_orders,
    }
    return render(request, "chef_templates/dashboard.html", context)

def pending_orders_partial(request):
    """
    Returns the pending orders partial for HTMX.
    """
    with schema_context(request.tenant.schema_name):
        pending_orders = Order.objects.select_related(
            "table"
        ).prefetch_related("order_items__menu_item").filter(status=Order.OrderStatus.SENT_TO_KITCHEN)

    return render(
        request,
        "chef_templates/partials/pending_orders.html",
        {"pending_orders": pending_orders}
    )
def accept_order(request, order_id):
    """
    Marks order as IN_PROGRESS (HTMX).
    """
    with schema_context(request.tenant.schema_name):
        order = get_object_or_404(Order, order_id=order_id)
        if order:
            print("Order found:", order)
            order.status = Order.OrderStatus.IN_PROGRESS
            order.save()

        active_orders = Order.objects.select_related(
            "table"
        ).prefetch_related("order_items__menu_item").filter(status=Order.OrderStatus.IN_PROGRESS)
        print("Active orders count:", active_orders.count())
        context = {"active_orders": active_orders}
        return render(
            request,
            "chef_templates/partials/active_orders.html",
            context
        )
        

def get_hotel_name(request):
     with schema_context(request.tenant.schema_name):
            hotel_name = HotelSettings.objects.first().hotel_name if HotelSettings.objects.exists() else 'Smart Hotel'
            return HttpResponse(hotel_name)

def complete_order(request, order_id):
    """
    Marks order as COMPLETED (HTMX).
    """
    with schema_context(request.tenant.schema_name):
        order = get_object_or_404(Order, order_id=order_id)
        order.status = Order.OrderStatus.COMPLETED
        order.save()

        active_orders = Order.objects.select_related(
            "table"
        ).prefetch_related("order_items__menu_item").filter(status=Order.OrderStatus.IN_PROGRESS)

    return render(
        request,
        "chef_templates/partials/active_orders.html",
        {"active_orders": active_orders}
    )
