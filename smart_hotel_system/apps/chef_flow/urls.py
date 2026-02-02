from django.urls import path
from . import views

app_name = 'chef_flow'

urlpatterns = [
    path('dashboard/', views.chef_dashboard, name='dashboard'),
    path('pending_orders_partial/', views.pending_orders_partial, name='pending_orders_partial'),
    path('active_orders_partial/', views.active_orders_partial, name='active_orders_partial'),
    path('hotel_name/', views.get_hotel_name, name='hotel_name'),
    path('accept/<int:order_id>/', views.accept_order, name='accept_order'),
    path('complete/<int:order_id>/', views.complete_order, name='complete_order'),
]
