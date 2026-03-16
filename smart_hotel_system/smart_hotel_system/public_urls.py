"""
Public URLs - accessible without tenant context
"""
from django.urls import path
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache
from django.contrib import admin

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
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>QuickDine Platform</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                text-align: center;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { margin: 0 0 1rem 0; font-size: 3rem; }
            p { margin: 0.5rem 0; font-size: 1.2rem; opacity: 0.9; }
            a {
                display: inline-block;
                margin-top: 2rem;
                padding: 1rem 2rem;
                background: white;
                color: #667eea;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
                transition: transform 0.2s;
            }
            a:hover { transform: scale(1.05); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍽️ QuickDine</h1>
            <p>Multi-Tenant Restaurant Management Platform</p>
            <p style="font-size: 1rem; opacity: 0.7;">Powered by Django Tenants</p>
            <a href="/admin/">Access Admin Panel →</a>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

urlpatterns = [
    path('', root_view, name='root'),
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),
]
