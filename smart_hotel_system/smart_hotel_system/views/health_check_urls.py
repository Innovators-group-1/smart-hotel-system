from django.urls import path
from . import health_check

urlpatterns = [
    path('health/',health_check.health_check, name='health')
]