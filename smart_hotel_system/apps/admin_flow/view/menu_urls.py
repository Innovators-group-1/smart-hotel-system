from django.urls import path
from . import menu

urlpatterns = [
    path('add-menu-item/', menu.add_menu_item, name='add_menu_item'),
    path('add-inbuilt-menu-item/', menu.add_inbuilt_menu_item, name='add_inbuilt_menu_item'),
    path('tap-add-inbuilt-menu-item/<str:item_id>/', menu.tap_add_inbuilt_menu_item, name='tap_add_inbuilt_menu_item'),
    path('add_new_category/', menu.add_new_category, name='add_new_category'),
    path('add-category/', menu.add_category, name='add_category'),
    path('menu_search/', menu.menu_search, name='menu_search'),
    path('menu_filter/<slug:slug>/', menu.menu_filter, name='menu_filter'),
    path('toggle-menu-availability/<str:item_id>/', menu.toggle_menu_availability, name='toggle_menu_availability'),
    path('edit-menu-item/<str:item_id>/', menu.edit_menu_item, name='menu_edit_form'),
    path('delete-menu-item/<str:item_id>/', menu.delete_menu_item, name='delete_menu_item'),
]