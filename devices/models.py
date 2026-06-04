from django.db import models
from django.conf import settings

# Create your models here.

class Device(models.Model):
    STATUS_CHOICES = [
        ('unknown', 'Unknown'),
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    name = models.CharField(max_length=100, verbose_name='Название')
    ip_address = models.GenericIPAddressField(unique=True, verbose_name='IP-адрес')
    vendor = models.CharField(max_length=100, verbose_name='Вендор')
    model = models.CharField(max_length=100, blank=True, verbose_name='Модель')
    location = models.CharField(max_length=150, blank=True, verbose_name='Локация')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unknown',
        verbose_name='Статус'
    )
    description = models.TextField(blank=True, verbose_name='Описание')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Коммутатор'
        verbose_name_plural = 'Коммутаторы'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.ip_address})'
    
class OperationLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('update', 'Изменение'),
        ('delete', 'Удаление'),
        ('bulk_delete', 'Массовое удаление'),

        ('info', 'Вывод информации'),
        ('backup', 'Создание backup'),
        ('ports_shutdown', 'Отключение портов'),
        ('ports_no_shutdown', 'Включение портов'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )

    device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Коммутатор'
    )

    device_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Название устройства'
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name='Действие'
    )

    message = models.TextField(verbose_name='Описание действия')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время')

    class Meta:
        verbose_name = 'Журнал действий'
        verbose_name_plural = 'Журнал действий'
        ordering = ['-created_at']

    def __str__(self):
        username = self.user.username if self.user else 'Unknown'
        return f'{self.get_action_display()} — {username} — {self.created_at}'
    
class NetworkTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('info', 'Вывести информацию'),
        ('backup', 'Создать backup'),
        ('ports_shutdown', 'Отключить порты'),
        ('ports_no_shutdown', 'Включить порты'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='network_tasks',
        verbose_name='Коммутатор'
    )

    task_type = models.CharField(
        max_length=30,
        choices=TASK_TYPE_CHOICES,
        verbose_name='Тип операции'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )

    selected_ports = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Выбранные порты'
    )

    command_preview = models.TextField(blank=True, verbose_name='Команда / playbook')
    stdout = models.TextField(blank=True, verbose_name='Вывод')
    stderr = models.TextField(blank=True, verbose_name='Ошибки')
    backup_file = models.CharField(max_length=255, blank=True, verbose_name='Файл backup')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Сетевая операция'
        verbose_name_plural = 'Сетевые операции'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_task_type_display()} — {self.device.name} — {self.status}'