from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache
from django.shortcuts import render

@never_cache
def root_view(request):
    """Root endpoint - welcome page"""
    return render(request, 'platform_template/quickdine.html')