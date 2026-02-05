# Checks the payment status of an order from the payment Attempt Model
from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404
from  apps.platform_admin_flow.models import PaymentAttempt
from apps.common_flow.models import Order
from django.db import connection
from contextlib import contextmanager

@contextmanager
def switch_schema(schema_name: str):
    prev_schema = connection.schema_name
    try:
        connection.set_schema(schema_name, True)
        yield
    finally:
        connection.set_schema(prev_schema, True)
def payment_status_view(request, reference):
    attempt = get_object_or_404(PaymentAttempt, reference=reference)

    # Default response
    response = {
        "status": attempt.status,
        "message": None,
        "order_id": None,
    }

    if attempt.status == "SUCCESS":
        # Switch into tenant schema to fetch order
        tenant_schema = getattr(attempt.tenant, "schema_name", "public")
        with switch_schema(tenant_schema):
            order = Order.objects.filter(payment_reference=attempt.reference).first()
            if order:
                response["order_id"] = order.pk
                response["message"] = "Payment confirmed"
            else:
                response["message"] = "Order not found, though payment succeeded"
    elif attempt.status == "FAILED":
        # provide insufficient funds message with money picture
        response["message"] = "💵 Insufficient funds"
    elif attempt.status == "CANCELLED":
        response["message"] = "Payment cancelled or timed out"
    else:
        response["message"] = "Payment still processing"

    return JsonResponse(response)
