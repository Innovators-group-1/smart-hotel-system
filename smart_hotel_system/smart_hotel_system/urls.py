
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
    """Simple health check that doesn't require tenant context"""
    return JsonResponse({"status": "ok"}, status=200)

urlpatterns = [
    # Respond to Chrome DevTools `.well-known` probe to avoid noisy 404s during development
    path('health/', health_check, name='health'),
    re_path(r'^\.well-known/appspecific/com\.chrome\.devtools\.json$', lambda req: JsonResponse({}, status=200)),
    path('admin/', admin.site.urls),
    path('platform/', include('apps.platform_admin_flow.urls', namespace='platform_admin_flow')),
    path('chef_dashboard/', include('apps.chef_flow.urls', namespace='chef_dashboard')),
    path('admin_dashboard/', include('apps.admin_flow.urls')),
    path('client_flow/',include('apps.client_flow.urls',namespace='client_flow')),
    path('chef_flow/', include('apps.chef_flow.urls', namespace='chef_flow')),
    path('admin_flow/', include('apps.admin_flow.urls')),
    path('', include('apps.client_flow.urls',namespace='client_root')),  # Root URL for client access
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
