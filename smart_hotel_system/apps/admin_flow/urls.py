from django.urls import path
from . import views

urlpatterns = [
    # GENERAL ADMIN DASHBOARD URLS
    path('main/', views.adminDashboard, name='admin-dashboard'),
    path('dashboard/',views.dashboard_partial, name='dashboard_partial'),
    path('orders/', views.orders_partial, name='orders_partial'),
    path('menu/', views.menu_partial, name='menu_partial'),
    path('reports/', views.reports_partial, name='reports_partial'),
    path('chefs/', views.chefs_partial, name='chefs_partial'),
    path('settings/', views.settings_partial, name='settings_partial'),


    # SPECIFIC FEATURES URLS
    path('hotel_name/' , views.get_hotel_name, name='get_hotel_name'),
    path('add-table/', views.add_table, name='add_table'),


    # SETTINGS PARTIAL URLS
    path('general-settings/', views.general_settings_partial, name='settings_general_partial'),
    path('display-settings/', views.display_settings_partial, name='settings_display_partial'),
    path('table-settings/', views.table_settings_partial, name='settings_table_partial'),
    path('payment-settings/', views.payment_settings_partial, name='settings_payment_partial'),
    path('user-management/', views.user_management_partial, name='settings_users_partial'),
    path('notification-settings/', views.notification_settings_partial, name='settings_notifications_partial'),
    path('system-preferences/', views.system_preferences_partial, name='settings_system_partial'),
    path('security-settings/', views.security_settings_partial, name='settings_security_partial'),
    path('advanced-settings/', views.advanced_settings_partial, name='settings_advanced_partial'),

    # SETTING FORMS PARTIAL URLS
    path('general-settings-form/', views.update_general_settings, name='update_general_settings'),
    path('display-settings-form/', views.update_display_settings, name='update_display_settings'),
    path('table-settings-form/', views.update_table_settings, name='update_table_settings'),
    path('payment-settings-form/', views.update_payment_settings, name='update_payment_settings'),
    path('user-management-form/', views.update_user_management, name='update_user_settings'),
    path('notification-settings-form/', views.update_notification_settings, name='update_notifications_settings'),
    path('system-preferences-form/', views.update_system_preferences, name='update_system_settings'),
    path('security-settings-form/', views.update_security_settings, name='update_security_settings'),
    path('advanced-settings-form/', views.update_advanced_settings, name='update_advanced_settings'),

]
