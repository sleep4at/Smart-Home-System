from django.utils import timezone
from rest_framework import serializers

from .constants import DeviceType
from .models import Device, DeviceData


class DeviceSerializer(serializers.ModelSerializer):
    """
    设备列表 / 详情用。
    """

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    # 在线状态直接读取模型字段，由 MQTT/LWT 与设备上报维护
    is_online = serializers.BooleanField(read_only=True)

    class Meta:
        model = Device
        fields = [
            "id",
            "name",
            "type",
            "type_display",
            "location",
            "is_online",
            "is_public",
            "current_state",
            "owner",
            "created_at",
            "updated_at",
        ]
        # [新增] 只读字段
        read_only_fields = ["id", "created_at", "updated_at", "is_online"]


class DeviceHistoryPointSerializer(serializers.ModelSerializer):
    """
    单个历史点，前端画图使用。
    """

    class Meta:
        model = DeviceData
        fields = ["timestamp", "data"]


class DeviceHistoryQuerySerializer(serializers.Serializer):
    """
    校验 /api/devices/{id}/history/ 的 query 参数。
    """

    RANGE_24H = "24h"
    RANGE_3D = "3d"
    RANGE_7D = "7d"

    RANGE_CHOICES = (
        (RANGE_24H, "24小时"),
        (RANGE_3D, "3天"),
        (RANGE_7D, "7天"),
    )

    range = serializers.ChoiceField(
        choices=RANGE_CHOICES, default=RANGE_24H, required=False
    )

    def get_time_range(self):
        """
        根据 range 返回起始时间。
        """
        range_value = self.validated_data.get("range") or self.RANGE_24H
        now = timezone.now()
        if range_value == self.RANGE_3D:
            delta = timezone.timedelta(days=3)
        elif range_value == self.RANGE_7D:
            delta = timezone.timedelta(days=7)
        else:
            delta = timezone.timedelta(hours=24)
        return now - delta, now

