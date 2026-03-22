from django.urls import path
from . import admin_views

urlpatterns = [
    path('super-admin/signup/', admin_views.super_admin_signup, name='super_admin_signup'),
    path('super-admin/login/', admin_views.super_admin_login, name='super_admin_login'),
    path('admin/', admin_views.admin_view, name='admin'), 
]