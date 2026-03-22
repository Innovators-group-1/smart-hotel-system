from django.urls import path
from . import home

urlpatterns = [
    path('', home.root_view, name='root'),
]