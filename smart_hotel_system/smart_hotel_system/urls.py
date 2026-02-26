"""smart_hotel_system URL Configuration"""
from django.urls import path, include, re_path
from django.conf import settings
from django.http import JsonResponse
from django.conf.urls.static import static

urlpatterns = [
    # Respond to Chrome DevTools `.well-known` probe to avoid noisy 404s during development
    re_path(r'^\.well-known/appspecific/com\.chrome\.devtools\.json$', lambda req: JsonResponse({}, status=200)),

    # Public/global routes
    path('', include('smart_hotel_system.public_urls')),   # root, health, admin

    # Tenant-specific routes
    path('platform/', include(('apps.platform_admin_flow.urls', 'platform_admin_flow'), namespace='platform_admin_flow')),
    path('chef_dashboard/', include(('apps.chef_flow.urls', 'chef_flow'), namespace='chef_dashboard')),
    path('admin_dashboard/', include('apps.admin_flow.urls')),
    path('client_flow/', include(('apps.client_flow.urls', 'client_flow'), namespace='client_flow')),
    path('chef_flow/', include(('apps.chef_flow.urls', 'chef_flow'), namespace='chef_flow')),
    path('admin_flow/', include('apps.admin_flow.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
