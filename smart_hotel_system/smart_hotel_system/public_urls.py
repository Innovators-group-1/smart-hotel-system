"""
Public URLs - accessible without tenant context
"""
from django.shortcuts import render
from django.urls import path
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache
from django.contrib import admin
from urllib3 import request
from django.contrib.auth.decorators import login_required

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

@login_required
def admin_view(request):
    """Admin endpoint - for demonstration purposes"""
    return render(request, 'platform_template/quickdine-admin.html')

@never_cache
def auth_view(request):
    """Authentication endpoint - for demonstration purposes"""
    return render(request, 'platform_template/quickdine-auth.html')

urlpatterns = [
    path('', root_view, name='root'),
    path('health/', health_check, name='health'),
    path('admin/', admin_view, name='admin'),
    path('auth/', auth_view, name='auth'),
]
