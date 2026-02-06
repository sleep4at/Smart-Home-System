"""
初始化所有设备的在线状态为离线。
用法：python3 manage.py init_device_online_status
"""
from django.core.management.base import BaseCommand

from devices.models import Device


class Command(BaseCommand):
    help = "将所有设备的 is_online 字段初始化为 False（离线状态）"

    def handle(self, *args, **options):
        count = Device.objects.update(is_online=False)
        self.stdout.write(
            self.style.SUCCESS(f"已将 {count} 个设备的在线状态设置为离线")
        )
