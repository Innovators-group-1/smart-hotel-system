from django.contrib import admin
from django.urls import path,include;
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('apps.client_flow.urls')),
    path('chef_dashboard/', include('apps.chef_flow.urls')),
    path('admin_dashboard/', include('apps.admin_flow.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
