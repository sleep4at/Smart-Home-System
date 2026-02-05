from django.conf import settings
from django.db import models
from django.utils import timezone     # <--- 新增
from datetime import timedelta        # <--- 新增

from .constants import DeviceType


class Device(models.Model):
    """
    设备基础信息和当前状态。
    """

    name = models.CharField("设备名称", max_length=100)
    type = models.CharField("设备类型", max_length=32, choices=DeviceType.choices)
    location = models.CharField("位置/房间", max_length=100, blank=True, default="")
    
    is_online = models.BooleanField("是否在线", default=False)
    # 当前状态：传感器或开关的最新值，JSON 结构由前端和模拟设备约定
    current_state = models.JSONField("当前状态", default=dict, blank=True)

    # 可选：设备归属用户（普通用户只看/控自己名下设备）
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="所属用户",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devices",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "设备"
        verbose_name_plural = "设备"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_type_display()})"

    # [新增]动态计算在线状态的属性（临时使用）
    @property
    def active_status(self):
        if not self.updated_at:
            return False
        # 如果 "现在时间" - "最后更新时间" < 90秒，则认为在线
        # 假设模拟器每30s发一次，如果90s没收到，说明掉线了
        threshold = timezone.now() - timedelta(seconds=90)
        return self.updated_at > threshold


class DeviceData(models.Model):
    """
    设备历史数据，用于“历史信息”图表。
    """

    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="data_points"
    )
    timestamp = models.DateTimeField(db_index=True)
    data = models.JSONField("数据内容")

    class Meta:
        verbose_name = "设备历史数据"
        verbose_name_plural = "设备历史数据"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.device_id} @ {self.timestamp}"

