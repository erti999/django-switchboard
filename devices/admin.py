from django.contrib import admin
from .models import Device, OperationLog, NetworkTask


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address', 'vendor', 'model', 'location', 'status')
    list_filter = ('status', 'vendor')
    search_fields = ('name', 'ip_address', 'location')


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'device_name', 'message')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'device_name', 'message')
    readonly_fields = ('user', 'device', 'device_name', 'action', 'message', 'created_at')


@admin.register(NetworkTask)
class NetworkTaskAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'device', 'task_type', 'status')
    list_filter = ('task_type', 'status', 'created_at')
    search_fields = ('device__name', 'device__ip_address', 'user__username', 'stdout', 'stderr')
    readonly_fields = (
        'user',
        'device',
        'task_type',
        'status',
        'selected_ports',
        'command_preview',
        'stdout',
        'stderr',
        'backup_file',
        'created_at',
        'updated_at',
    )