from django.urls import path
from . import orders

urlpatterns = [
    # ORDER MANAGEMENT URLS
    path('orders_search/', orders.orders_search, name='orders_search'),

    # filter orders by status
    path('orders_filter/<slug:status>/', orders.orders_filter_by_status, name='orders_filter'),

    # filter by payment status
    path('payment_status_filter/<slug:slug>/', orders.payment_status_filter, name='payment_status_filter'),

    # get order list partial
    path('order_list_partial/', orders.order_list_partial, name='order_list_partial'),

    # get updated row partial
    path('order_row_partial/<int:order_id>/', orders.order_row_partial, name='order_row_partial'),

    # get order details partial
    path('order_details_partial/<int:order_id>/', orders.order_details_partial, name='order_details_partial'),

    # Paging for orders
    path('orders_page/<int:page_number>/', orders.orders_page, name='orders_page'),

    # order details partial urls
    path('verify_payment/<int:order_id>/', orders.verify_payment, name='verify_payment'),
    path('mpesa_verification_partial/<int:order_id>/', orders.mpesa_verification_partial, name='mpesa_verification_partial'),
    path('confirm_payment/<int:order_id>/', orders.confirm_payment, name='confirm_payment'),
    path('mark_unpaid/<int:order_id>/', orders.mark_unpaid, name='mark_unpaid'),
    path('send_to_kitchen/<int:order_id>/', orders.send_to_kitchen, name='send_to_kitchen'),
    path('print_receipt/<int:order_id>/', orders.print_receipt, name='print_receipt'),
    path('cancel_order/<int:order_id>/', orders.cancel_order, name='cancel_order'),
]