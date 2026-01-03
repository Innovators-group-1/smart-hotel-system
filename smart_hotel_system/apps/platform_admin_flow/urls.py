# apps/platform_admin_flow/urls.py
from django.urls import path
from apps.platform_admin_flow.views.mpesa_callback import mpesa_callback

urlpatterns = [
    path("mpesa/callback/", mpesa_callback, name="mpesa_callback"),
]
# End of apps/platform_admin_flow/urls.py