from django.shortcuts import render, get_object_or_404, redirect
from apps.common_flow.models import Order
from django_tenants.utils import schema_context

def chef_dashboard(request):
    """
    Main dashboard view.
    Fetches all orders grouped by their kitchen status.
    """
    with schema_context(request.tenant.schema_name):
     pending_orders = Order.objects.select_related("table").prefetch_related("order_items__menu_item").filter(
        status=Order.OrderStatus.PENDING
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
        "active_orders": active_orders,
        "completed_orders": completed_orders,
        "urgent_orders": urgent_orders,
    }

    return render(request, "chef_templates/dashboard.html", context)

def accept_order(request, order_id):
    """
    Marks order as IN_PROGRESS (HTMX).
    """
    with schema_context(request.tenant.schema_name):
        order = get_object_or_404(Order, order_id=order_id)
        order.status = Order.OrderStatus.IN_PROGRESS
        order.save()

        active_orders = Order.objects.select_related(
            "table"
        ).prefetch_related("order_items__menu_item").filter(status=Order.OrderStatus.IN_PROGRESS)

    return render(
        request,
        "chef_templates/partials/active_orders.html",
        {"active_orders": active_orders}
    )


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
