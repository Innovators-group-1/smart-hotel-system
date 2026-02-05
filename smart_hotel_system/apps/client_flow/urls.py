from django.urls import path
from . import views

app_name = 'client_flow'

urlpatterns = [
    path('menu/<int:table_number>/', views.menu_view, name='menu'),
    path('menu_search/', views.menu_search_view, name='menu_search'),
    path('menu_redirect/', views.menu_redirect_view, name='menu_redirect'),
    path('seat_selector/', views.seat_selector_view, name='seat_selector'),
    path('set_seat/', views.set_seat_view, name='set_seat'),
    path('menu_filter/<int:category_id>/', views.menu_filter_view, name='menu_category_filter'),
    path('all_items/', views.all_menu_items_view, name='all_items'),
    path('cart/', views.cart_view, name='cart'),
    path('cart_count/', views.cart_count_view, name='cart_count'),
    path('hotel_name/', views.hotel_name_view, name='hotel_name'),
    path('add_to_cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('update_cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/mpesa_process/', views.mpesa_checkout_view, name='mpesa_process'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'),
    path('track/<int:order_id>/', views.order_tracking_view, name='order_tracking'),
    path('load_subcategories/<int:main_id>/', views.load_subcategories, name='load_subcategories'),
]
