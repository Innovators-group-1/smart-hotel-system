"""
URL configuration for smart_hotel_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include;

urlpatterns = [
    path('admin/', admin.site.urls),
    path('client_flow/',include('apps.client_flow.urls')),
    path('chef_flow/', include('apps.chef_flow.urls')),
    path('admin_flow/', include('apps.admin_flow.urls')),
    path('system_flow/',include('apps.system_flow.urls')),
]
