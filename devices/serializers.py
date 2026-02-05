from django.utils import timezone
from rest_framework import serializers

from .constants import DeviceType
from .models import Device, DeviceData


class DeviceSerializer(serializers.ModelSerializer):
    """
    设备列表 / 详情用。
    """

    type_display = serializers.CharField(source="get_type_display", read_only=True)

    # [新增] 使用 SerializerMethodField 覆盖默认的模型字段
    # 这样读取时会调用下方的 get_is_online 方法，而不是直接读数据库的 is_online 字段
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = [
            "id",
            "name",
            "type",
            "type_display",
            "location",
            "is_online",
            "current_state",
            "owner",
            "created_at",
            "updated_at",
        ]
        # [新增] 只读字段
        read_only_fields = ["id", "created_at", "updated_at", "is_online"]

    # [新增] 定义计算逻辑
    def get_is_online(self, obj) -> bool:
        # 这里调用我们在 models.py 里新写的 @property active_status
        # 如果你还没修改 models.py，请务必先修改，否则这里会报错
        if hasattr(obj, 'active_status'):
            return obj.active_status
        return False


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

