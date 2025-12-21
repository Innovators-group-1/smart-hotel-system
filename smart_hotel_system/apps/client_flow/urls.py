from django.urls import path
from . import views

app_name = 'client_flow'

urlpatterns = [
    path('menu/', views.menu_view, name='menu'),
    path('menu_filter/<int:category_id>/', views.menu_filter_view, name='menu_category_filter'),
    path('all_items/', views.all_menu_items_view, name='all_items'),
    path('cart/', views.cart_view, name='cart'),
    path('hotel_name/', views.hotel_name_view, name='hotel_name'),
    path('add_to_cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('update_cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'),
    path('track/<int:order_id>/', views.order_tracking_view, name='order_tracking'),
]
