from django.contrib import admin
from django.urls import path, include
from . import views

from django.contrib.auth import views as auth_views

# urlpatterns = [
#     path('', views.dashboard, name='dashboard'),
#     path('login/', views.login_view, name='login'),
#     path('register/', views.register_view, name='register'),
#     path('devices/', views.devices_view, name='devices'),
#     path('logout/', auth_views.LogoutView.as_view(next_page='dashboard'), name='logout'),
#     path('api/devices/', views.api_devices, name='api_devices'),
#     path('api/devices/<uuid:device_id>/toggle/', views.api_toggle_device, name='api_toggle_device'),
#     path('api/energy/', views.api_energy_data, name='api_energy'),
# ]

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('devices/', views.devices_view, name='devices'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # APIs
    path('api/devices/', views.api_devices, name='api_devices'),
    path('api/devices/<uuid:device_id>/toggle/', views.api_toggle_device, name='api_toggle_device'),
    path('api/energy/', views.api_energy_data, name='api_energy'),
    path('api/total/', views.api_total_usage, name='api_total'),  # ✅ NEW
]