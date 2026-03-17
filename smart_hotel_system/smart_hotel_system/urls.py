"""smart_hotel_system URL Configuration"""
from django.shortcuts import render
from django.urls import path, include, re_path
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.conf.urls.static import static
from django.contrib import admin
from django.views.decorators.cache import never_cache

# Public URL handlers (defined inline to ensure they're available on all schemas)
@never_cache
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        "status": "healthy",
        "service": "QuickDine Multi-Tenant Platform"
    }, status=200)

@never_cache
def root_view(request):
    """Root endpoint - welcome page"""
    return render(request, 'platform_template/quickdine.html')


urlpatterns = [
    # Respond to Chrome DevTools `.well-known` probe to avoid noisy 404s during development
    re_path(r'^\.well-known/appspecific/com\.chrome\.devtools\.json$', lambda req: JsonResponse({}, status=200)),

    # Public/global routes - inline to ensure availability on all schemas
    path('', root_view, name='root'),
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),

    # Tenant-specific routes
    path('platform/', include(('apps.platform_admin_flow.urls', 'platform_admin_flow'), namespace='platform_admin_flow')),
    path('chef_dashboard/', include(('apps.chef_flow.urls', 'chef_flow'), namespace='chef_dashboard')),
    path('admin_dashboard/', include('apps.admin_flow.urls')),
    path('client_flow/', include(('apps.client_flow.urls', 'client_flow'), namespace='client_flow')),
    path('chef_flow/', include(('apps.chef_flow.urls', 'chef_flow'), namespace='chef_flow')),
    path('admin_flow/', include('apps.admin_flow.urls')),
]

# Serve static and media files (WhiteNoise handles this in production)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
