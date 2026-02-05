# apps/platform_admin_flow/urls.py
from django.urls import path
from apps.platform_admin_flow.views.mpesa_callback import mpesa_callback
from apps.platform_admin_flow.views.payment_status import payment_status_view

app_name = "platform_admin_flow"
urlpatterns = [
    path("mpesa/callback/", mpesa_callback, name="mpesa_callback"),
    path("payment/status/<str:reference>/", payment_status_view, name="payment_status"),
]
# End of apps/platform_admin_flow/urls.py