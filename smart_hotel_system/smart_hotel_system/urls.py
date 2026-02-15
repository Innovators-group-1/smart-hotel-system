
"""smart_hotel_system URL Configuration"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.cache import never_cache

# Health check view that doesn't require tenant context
@never_cache
def health_check(request):
    """Health check endpoint for Control Plane"""
    return JsonResponse({
        "status": "healthy",
        "service": "quickdine"
    }, status=200)

@never_cache
def root_view(request):
    """Root endpoint - redirect or info page"""
    return JsonResponse({
        "message": "QuickDine Multi-Tenant Platform",
        "status": "running"
    }, status=200)

urlpatterns = [
    # Respond to Chrome DevTools `.well-known` probe to avoid noisy 404s during development
    re_path(r'^\.well-known/appspecific/com\.chrome\.devtools\.json$', lambda req: JsonResponse({}, status=200)),
    path('health/', health_check, name='health'),
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('platform/', include('apps.platform_admin_flow.urls', namespace='platform_admin_flow')),
    path('chef_dashboard/', include('apps.chef_flow.urls', namespace='chef_dashboard')),
    path('admin_dashboard/', include('apps.admin_flow.urls')),
    path('client_flow/',include('apps.client_flow.urls',namespace='client_flow')),
    path('chef_flow/', include('apps.chef_flow.urls', namespace='chef_flow')),
    path('admin_flow/', include('apps.admin_flow.urls')),
    path('', include('apps.client_flow.urls',namespace='client_root')),  # Root URL for client access
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
