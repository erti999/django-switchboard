from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect

from .forms import DeviceForm
from .models import Device, OperationLog, NetworkTask
from django.utils import timezone
import json
import os
import re
import subprocess
import tempfile


PORT_CHOICES = [
    {'label': 'Gi0/0', 'value': 'GigabitEthernet0/0'},
    {'label': 'Gi0/1', 'value': 'GigabitEthernet0/1'},
    {'label': 'Gi0/2', 'value': 'GigabitEthernet0/2'},
    {'label': 'Gi0/3', 'value': 'GigabitEthernet0/3'},

    {'label': 'Gi1/0', 'value': 'GigabitEthernet1/0'},
    {'label': 'Gi1/1', 'value': 'GigabitEthernet1/1'},
    {'label': 'Gi1/2', 'value': 'GigabitEthernet1/2'},
    {'label': 'Gi1/3', 'value': 'GigabitEthernet1/3'},

    {'label': 'Gi2/0', 'value': 'GigabitEthernet2/0'},
    {'label': 'Gi2/1', 'value': 'GigabitEthernet2/1'},
    {'label': 'Gi2/2', 'value': 'GigabitEthernet2/2'},
    {'label': 'Gi2/3', 'value': 'GigabitEthernet2/3'},

    {'label': 'Gi3/0', 'value': 'GigabitEthernet3/0'},
    {'label': 'Gi3/1', 'value': 'GigabitEthernet3/1'},
    {'label': 'Gi3/2', 'value': 'GigabitEthernet3/2'},
    {'label': 'Gi3/3', 'value': 'GigabitEthernet3/3'},
]


def log_operation(user, action, device=None, message=''):
    OperationLog.objects.create(
        user=user if user.is_authenticated else None,
        device=device,
        device_name=str(device) if device else '',
        action=action,
        message=message,
    )


@login_required
@permission_required('devices.view_device', raise_exception=True)
def device_list(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_devices')

        if action == 'bulk_delete':
            if not request.user.has_perm('devices.delete_device'):
                return HttpResponseForbidden('Недостаточно прав для удаления устройств.')

            if selected_ids:
                devices_to_delete = list(Device.objects.filter(pk__in=selected_ids))
                deleted_count = len(devices_to_delete)

                for device in devices_to_delete:
                    log_operation(
                        request.user,
                        'bulk_delete',
                        device,
                        f'Массовое удаление коммутатора {device.name} ({device.ip_address})'
                    )

                Device.objects.filter(pk__in=selected_ids).delete()
                messages.success(request, f'Удалено устройств: {deleted_count}')
            else:
                messages.warning(request, 'Вы не выбрали ни одного коммутатора.')

            return redirect('devices:device_list')

    devices = Device.objects.all()

    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        devices = devices.filter(
            Q(name__icontains=search_query) |
            Q(ip_address__icontains=search_query) |
            Q(vendor__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    if status_filter:
        devices = devices.filter(status=status_filter)

    context = {
        'devices': devices,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_count': Device.objects.count(),
        'online_count': Device.objects.filter(status='online').count(),
        'offline_count': Device.objects.filter(status='offline').count(),
        'unknown_count': Device.objects.filter(status='unknown').count(),
    }

    return render(request, 'devices/device_list.html', context)


@login_required
@permission_required('devices.view_device', raise_exception=True)
def device_detail(request, pk):
    device = get_object_or_404(Device, pk=pk)

    if request.user.has_perm('devices.view_networktask'):
        recent_tasks = device.network_tasks.all()[:5]
    else:
        recent_tasks = []

    context = {
        'device': device,
        'port_choices': PORT_CHOICES,
        'recent_tasks': recent_tasks,
    }

    return render(request, 'devices/device_detail.html', context)


@login_required
@permission_required('devices.add_device', raise_exception=True)
def device_create(request):
    if request.method == 'POST':
        form = DeviceForm(request.POST)

        if form.is_valid():
            device = form.save()

            log_operation(
                request.user,
                'create',
                device,
                f'Добавлен коммутатор {device.name} ({device.ip_address})'
            )

            messages.success(request, 'Коммутатор успешно добавлен.')
            return redirect('devices:device_list')
    else:
        form = DeviceForm()

    return render(request, 'devices/device_form.html', {
        'form': form,
        'title': 'Добавить коммутатор',
        'button_text': 'Добавить',
    })


@login_required
@permission_required('devices.change_device', raise_exception=True)
def device_update(request, pk):
    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        form = DeviceForm(request.POST, instance=device)

        if form.is_valid():
            device = form.save()

            log_operation(
                request.user,
                'update',
                device,
                f'Обновлён коммутатор {device.name} ({device.ip_address})'
            )

            messages.success(request, 'Коммутатор успешно обновлён.')
            return redirect('devices:device_detail', pk=device.pk)
    else:
        form = DeviceForm(instance=device)

    return render(request, 'devices/device_form.html', {
        'form': form,
        'title': 'Редактировать коммутатор',
        'button_text': 'Сохранить',
    })


@login_required
@permission_required('devices.delete_device', raise_exception=True)
def device_delete(request, pk):
    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        log_operation(
            request.user,
            'delete',
            device,
            f'Удалён коммутатор {device.name} ({device.ip_address})'
        )

        device.delete()
        messages.success(request, 'Коммутатор успешно удалён.')
        return redirect('devices:device_list')

    return render(request, 'devices/device_confirm_delete.html', {'device': device})


@login_required
@permission_required('devices.view_device', raise_exception=True)
def operation_list(request):
    logs = OperationLog.objects.select_related('user', 'device').all()

    search_query = request.GET.get('q', '')
    action_filter = request.GET.get('action', '')

    if search_query:
        logs = logs.filter(
            Q(user__username__icontains=search_query) |
            Q(device_name__icontains=search_query) |
            Q(message__icontains=search_query)
        )

    if action_filter:
        logs = logs.filter(action=action_filter)

    context = {
        'logs': logs[:100],
        'search_query': search_query,
        'action_filter': action_filter,
        'action_choices': OperationLog.ACTION_CHOICES,
    }

    return render(request, 'devices/operation_list.html', context)


@login_required
def about(request):
    return render(request, 'devices/about.html')


def safe_backup_filename(device, now):
    safe_name = re.sub(r'[^a-zA-Z0-9_.-]+', '_', device.name).strip('_')
    safe_ip = str(device.ip_address).replace(':', '_')
    return f'{safe_name or "device"}_{safe_ip}_{now}.txt'


def build_ansible_inventory(device):
    host_vars = {
        'ansible_host': str(device.ip_address),
        'ansible_connection': 'network_cli',
        'ansible_network_os': 'cisco.ios.ios',
        'ansible_user': settings.ANSIBLE_USER,
        'ansible_password': settings.ANSIBLE_PASSWORD,
        'ansible_command_timeout': settings.ANSIBLE_TIMEOUT,
    }

    if settings.ANSIBLE_BECOME_PASSWORD:
        host_vars.update({
            'ansible_become': True,
            'ansible_become_method': 'enable',
            'ansible_become_password': settings.ANSIBLE_BECOME_PASSWORD,
        })

    return {
        'all': {
            'children': {
                'switches': {
                    'hosts': {
                        'target': host_vars,
                    },
                },
            },
        },
    }


def execute_ansible_network_task(task):
    device = task.device
    now = timezone.now().strftime('%Y%m%d_%H%M%S')
    playbooks = {
        'info': 'get_info.yml',
        'backup': 'backup_config.yml',
        'ports_shutdown': 'manage_ports.yml',
        'ports_no_shutdown': 'manage_ports.yml',
    }

    if not settings.ANSIBLE_USER or not settings.ANSIBLE_PASSWORD:
        task.status = 'failed'
        task.stderr = 'ANSIBLE_USER и ANSIBLE_PASSWORD должны быть указаны в .env.'
        task.save()
        return

    playbook_path = settings.ANSIBLE_PLAYBOOK_DIR / playbooks[task.task_type]
    extra_vars = {}

    if task.task_type == 'backup':
        settings.ANSIBLE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = settings.ANSIBLE_BACKUP_DIR / safe_backup_filename(device, now)
        task.backup_file = str(backup_path)
        extra_vars['backup_file'] = str(backup_path)

    if task.task_type in ['ports_shutdown', 'ports_no_shutdown']:
        extra_vars['selected_ports'] = task.selected_ports
        extra_vars['port_action'] = 'shutdown' if task.task_type == 'ports_shutdown' else 'no shutdown'

    task.status = 'running'
    task.command_preview = (
        f'ansible-playbook -i <generated inventory> {playbook_path.name} '
        f'--limit {device.ip_address}'
    )
    task.save()

    with tempfile.TemporaryDirectory() as temp_dir:
        inventory_path = os.path.join(temp_dir, 'inventory.json')

        with open(inventory_path, 'w', encoding='utf-8') as inventory_file:
            json.dump(build_ansible_inventory(device), inventory_file, ensure_ascii=False)

        command = [
            'ansible-playbook',
            '-i',
            inventory_path,
            str(playbook_path),
        ]

        if extra_vars:
            command.extend(['--extra-vars', json.dumps(extra_vars, ensure_ascii=False)])

        env = os.environ.copy()
        env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=settings.ANSIBLE_TIMEOUT,
                env=env,
            )
        except FileNotFoundError:
            task.status = 'failed'
            task.stderr = 'Команда ansible-playbook не найдена. Установи Ansible на сервере/ноуте.'
            task.save()
            return
        except subprocess.TimeoutExpired as exc:
            task.status = 'failed'
            task.stdout = exc.stdout or ''
            task.stderr = exc.stderr or f'Ansible не завершился за {settings.ANSIBLE_TIMEOUT} секунд.'
            task.save()
            return

    task.stdout = result.stdout
    task.stderr = result.stderr
    task.status = 'success' if result.returncode == 0 else 'failed'
    task.save()


@login_required
@permission_required('devices.view_device', raise_exception=True)
def network_task_list(request):
    tasks = NetworkTask.objects.select_related('user', 'device').all()[:100]

    context = {
        'tasks': tasks,
    }

    return render(request, 'devices/network_task_list.html', context)


@login_required
@permission_required('devices.view_device', raise_exception=True)
def network_task_detail(request, pk):
    task = get_object_or_404(
        NetworkTask.objects.select_related('user', 'device'),
        pk=pk
    )

    return render(request, 'devices/network_task_detail.html', {
        'task': task,
    })


@login_required
@permission_required('devices.change_device', raise_exception=True)
def network_task_create(request, pk):
    device = get_object_or_404(Device, pk=pk)

    if request.method != 'POST':
        return redirect('devices:device_detail', pk=device.pk)

    task_type = request.POST.get('task_type')
    allowed_task_types = dict(NetworkTask.TASK_TYPE_CHOICES)

    if task_type not in allowed_task_types:
        messages.error(request, 'Неизвестный тип операции.')
        return redirect('devices:device_detail', pk=device.pk)

    selected_ports = []

    if task_type in ['ports_shutdown', 'ports_no_shutdown']:
        selected_ports = request.POST.getlist('ports')
        allowed_ports = [port['value'] for port in PORT_CHOICES]

        if not selected_ports:
            messages.warning(request, 'Выберите хотя бы один порт.')
            return redirect('devices:device_detail', pk=device.pk)

        if len(selected_ports) > 16:
            messages.error(request, 'Можно выбрать максимум 16 портов.')
            return redirect('devices:device_detail', pk=device.pk)

        for port in selected_ports:
            if port not in allowed_ports:
                messages.error(request, f'Недопустимый порт: {port}')
                return redirect('devices:device_detail', pk=device.pk)

    task = NetworkTask.objects.create(
        user=request.user,
        device=device,
        task_type=task_type,
        selected_ports=selected_ports,
        status='pending',
    )

    execute_ansible_network_task(task)

    log_operation(
        request.user,
        task_type,
        device,
        f'Создана операция: {task.get_task_type_display()} для {device.name}'
    )

    messages.success(request, 'Операция создана.')
    return redirect('devices:network_task_detail', pk=task.pk)
