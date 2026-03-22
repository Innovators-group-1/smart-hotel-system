"""
Public URLs - accessible without tenant context
"""
from django.urls import path,include
from . import views

urlpatterns = [
    path('', include('smart_hotel_system.views.home_urls')),
    path('', include('smart_hotel_system.views.admin_urls')),
    path('health/', views.health_check, name='health'), 
]
