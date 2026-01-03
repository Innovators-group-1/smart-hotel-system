from apps.platform_admin_flow.models import PaymentIndex
from apps.common_flow.models import Order
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import json
import datetime
from django.utils import timezone
from contextlib import contextmanager


@contextmanager
def switch_schema(schema_name: str):
    prev_schema = connection.schema_name
    try:
        connection.set_schema(schema_name, True)
        yield
    finally:
        connection.set_schema(prev_schema, True)

# Mpesa STK Callback View
@csrf_exempt
def mpesa_callback(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method.")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON data.")

    try:
        stk = data["Body"]["stkCallback"]
        checkout_request_id = stk["CheckoutRequestID"]
        result_code = stk["ResultCode"]
        items = {i["Name"]: i.get("Value") for i in stk.get("CallbackMetadata", {}).get("Item", [])}
    except Exception:
        return HttpResponseBadRequest("Malformed STK payload.")

    index = PaymentIndex.objects.filter(checkout_request_id=checkout_request_id).first()
    if not index:
        return HttpResponseBadRequest("Payment index not found.")

    # Switch to the tenant schema for order updates
    tenant_schema = getattr(index.tenant, "schema_name", "public")
    with switch_schema(tenant_schema):
        order = Order.objects.filter(order_id=index.order_ref).first()
        if not order:
            return HttpResponseBadRequest("Order not found in tenant schema.")

        # Update order fields based on payload
        order.mpesa_amount = items.get("Amount")
        order.mpesa_receipt = items.get("MpesaReceiptNumber")
        order.mpesa_phone = items.get("PhoneNumber")
        txn_date = items.get("TransactionDate")
        if txn_date:
            try:
                parsed = datetime.datetime.strptime(str(txn_date), '%Y%m%d%H%M%S')
                order.mpesa_txn_date = timezone.make_aware(parsed)
            except ValueError:
                order.mpesa_txn_date = None
        else:
            order.mpesa_txn_date = None
        order.mpesa_result_code = result_code

        # Your status logic here
        if result_code == 0:
            order.payment_status = Order.PaymentStatus.VERIFYING  # or PAID after cashier verification
        else:
            order.payment_status = Order.PaymentStatus.FAILED

        order.save()

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback processed"})
