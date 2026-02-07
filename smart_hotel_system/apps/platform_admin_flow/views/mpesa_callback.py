# filepath: /home/stephen-nyansoho-machera/Desktop/Smart-hotel/smart-hotel-system/smart_hotel_system/apps/platform_admin_flow/views/mpesa_callback.py
from apps.platform_admin_flow.models import PaymentIndex, PaymentAttempt
from apps.common_flow.models import Order, OrderItem, Table, Menu as MenuItem
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import json
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def switch_schema(schema_name: str):
    prev_schema = connection.schema_name
    try:
        connection.set_schema(schema_name, True)
        yield
    finally:
        connection.set_schema(prev_schema, True)

@csrf_exempt
def mpesa_callback(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        stk_callback = data["Body"]["stkCallback"]

        result_code = stk_callback["ResultCode"]
        result_desc = stk_callback["ResultDesc"]
        merchant_request_id = stk_callback["MerchantRequestID"]
        checkout_request_id = stk_callback["CheckoutRequestID"]

        # Find PaymentAttempt in public schema
        attempt = PaymentAttempt.objects.filter(merchant_request_id=merchant_request_id).first()
        
        if not attempt:
            logger.warning(f"PaymentAttempt not found for merchant_request_id: {merchant_request_id}")
            return JsonResponse({"ResultCode": 1, "ResultDesc": "PaymentAttempt not found"}, status=404)
        
        # Extract metadata
        metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        amount = phone = transaction_id = txn_date = None
        for item in metadata:
            if item["Name"] == "Amount":
                amount = item["Value"]
            elif item["Name"] == "PhoneNumber":
                phone = item["Value"]
            elif item["Name"] == "MpesaReceiptNumber":
                transaction_id = item["Value"]
            elif item["Name"] == "TransactionDate":
                txn_date = item["Value"]

        # Get tenant schema
        tenant_schema = getattr(attempt.tenant, "schema_name", "public")
        order_ref = None

        # Switch to tenant schema for order creation
        with switch_schema(tenant_schema):
            if result_code == 0:
                try:
                    # Get table
                    table = get_object_or_404(Table, number=attempt.table_number)
                    
                    # Create Order
                    order = Order.objects.create(
                        table=table,  # Use table object, not number
                        seat=attempt.seat,
                        status=Order.OrderStatus.PENDING,
                        payment_status=Order.PaymentStatus.PAID,
                        payment_method=Order.PaymentMethod.M_PESA,
                        payment_number=attempt.phone_number,
                        payment_reference=attempt.reference,
                        special_requests='',
                    )
                    order_ref = order.pk

                    # Create OrderItems
                    cart = attempt.cart_data
                    if isinstance(cart, str):
                        cart = json.loads(cart)  # Handle if cart_data is JSON string
                    
                    item_ids = [int(i) for i in cart.keys()]
                    items = MenuItem.objects.filter(menu_item_id__in=item_ids)
                    
                    for item in items:
                        quantity = cart[str(item.menu_item_id)]
                        subtotal = item.price * quantity
                        OrderItem.objects.create(
                            order=order,
                            menu_item=item,
                            quantity=quantity,
                            total_price=subtotal,
                        )
                    
                    logger.info(f"Order created successfully: {order.pk}")
                except Exception as e:
                    logger.error(f"Error creating order: {str(e)}", exc_info=True)
                    raise

        # Update PaymentAttempt in public schema (outside tenant context)
        attempt.status = "SUCCESS" if result_code == 0 else "FAILED"
        if result_code == 1019:
            attempt.status = "CANCELLED"
        attempt.save()

        # Create PaymentIndex in public schema (it's a shared app)
        PaymentIndex.objects.create(
            tenant=attempt.tenant,
            order_ref=order_ref,
            account_reference=attempt.reference,
            checkout_request_id=checkout_request_id,
            merchant_request_id=merchant_request_id,
        )

        if result_code == 0:
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Payment successful"})
        elif result_code == 1:
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Insufficient funds"})
        elif result_code == 1019:
            return JsonResponse({"ResultCode": 1019, "ResultDesc": "Cancelled or timed out"})
        else:
            return JsonResponse({"ResultCode": result_code, "ResultDesc": result_desc})

    except Exception as e:
        logger.error(f"Callback error: {str(e)}", exc_info=True)
        return JsonResponse({"ResultCode": 1, "ResultDesc": str(e)}, status=500)