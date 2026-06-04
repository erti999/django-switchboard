from rest_framework import permissions, viewsets

from .models import Device
from .serializers import DeviceSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    filterset_fields = ['status', 'vendor', 'location']
    search_fields = ['name', 'ip_address', 'vendor', 'model', 'location']
    ordering_fields = ['name', 'ip_address', 'created_at', 'updated_at']
    ordering = ['name']