from django import forms
from .models import Device


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = [
            'name',
            'ip_address',
            'vendor',
            'model',
            'location',
            'status',
            'description',
        ]

        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }