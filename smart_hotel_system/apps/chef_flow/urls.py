from django.urls import path
from . import views

app_name = 'chef_flow'

urlpatterns = [
    path('dashboard/', views.chef_dashboard, name='dashboard'),
    path('accept/<int:order_id>/', views.accept_order, name='accept_order'),
    path('complete/<int:order_id>/', views.complete_order, name='complete_order'),
]
