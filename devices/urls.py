from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .api_views import DeviceViewSet


app_name = 'devices'

router = DefaultRouter()
router.register('devices', DeviceViewSet, basename='api-devices')


urlpatterns = [
    path('', views.device_list, name='device_list'),
    path('devices/add/', views.device_create, name='device_create'),
    path('devices/<int:pk>/', views.device_detail, name='device_detail'),
    path('devices/<int:pk>/edit/', views.device_update, name='device_update'),
    path('devices/<int:pk>/delete/', views.device_delete, name='device_delete'),

    path('operations/', views.operation_list, name='operation_list'),
    path('tasks/', views.network_task_list, name='network_task_list'),
    path('tasks/<int:pk>/', views.network_task_detail, name='network_task_detail'),
    path('devices/<int:pk>/tasks/create/', views.network_task_create, name='network_task_create'),

    path('about/', views.about, name='about'),

    path('api/', include(router.urls)),
]