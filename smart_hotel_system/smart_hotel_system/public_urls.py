"""
Public URLs - accessible without tenant context
"""
from django.urls import path,include

urlpatterns = [
    path('', include('smart_hotel_system.views.home_urls')),
    path('', include('smart_hotel_system.views.admin_urls')),
    path('', include('smart_hotel_system.views.health_check_urls'))
]
