from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache

@never_cache
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        "status": "healthy",
        "service": "QuickDine Multi-Tenant Platform"
    }, status=200)
