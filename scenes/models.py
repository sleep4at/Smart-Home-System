from django.conf import settings
from django.db import models

from devices.models import Device


class SceneRule(models.Model):
    """
    场景规则（智能联动）：当满足某个条件时，自动执行某个动作。
    """

    # 触发类型
    TRIGGER_THRESHOLD_ABOVE = "THRESHOLD_ABOVE"  # 阈值上限触发：值 > 阈值
    TRIGGER_THRESHOLD_BELOW = "THRESHOLD_BELOW"  # 阈值下限触发：值 < 阈值
    TRIGGER_RANGE_OUT = "RANGE_OUT"  # 区间外触发：值不在 [min, max] 范围内
    TRIGGER_TIME_STATE = "TIME_STATE"  # 时间+状态组合触发

    TRIGGER_CHOICES = (
        (TRIGGER_THRESHOLD_ABOVE, "高于阈值"),
        (TRIGGER_THRESHOLD_BELOW, "低于阈值"),
        (TRIGGER_RANGE_OUT, "超出范围"),
        (TRIGGER_TIME_STATE, "时间+状态组合"),
    )

    # 动作类型
    ACTION_TOGGLE = "TOGGLE"  # 开关切换
    ACTION_SET_TEMP = "SET_TEMP"  # 设置温度（空调）
    ACTION_SET_FAN_SPEED = "SET_FAN_SPEED"  # 设置风扇档位（1/2/3）
    ACTION_TURN_ON = "TURN_ON"  # 开启
    ACTION_TURN_OFF = "TURN_OFF"  # 关闭

    ACTION_CHOICES = (
        (ACTION_TOGGLE, "切换开关"),
        (ACTION_SET_TEMP, "设置温度"),
        (ACTION_SET_FAN_SPEED, "设置风扇档位"),
        (ACTION_TURN_ON, "开启设备"),
        (ACTION_TURN_OFF, "关闭设备"),
    )

    name = models.CharField("规则名称", max_length=100)
    enabled = models.BooleanField("是否启用", default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="所属用户",
        on_delete=models.CASCADE,
        related_name="scene_rules",
    )

    # 触发条件
    trigger_type = models.CharField("触发类型", max_length=32, choices=TRIGGER_CHOICES)
    trigger_device = models.ForeignKey(
        Device,
        verbose_name="触发设备",
        on_delete=models.CASCADE,
        related_name="trigger_rules",
    )
    trigger_field = models.CharField(
        "触发字段", max_length=50, help_text="例如：temp（温度）、humi（湿度）"
    )
    # 触发值：对于阈值类型是单个数值，对于区间类型是 JSON {"min": X, "max": Y}
    trigger_value = models.JSONField("触发值", help_text="阈值或范围值")

    # 时间条件（可选，用于 TIME_STATE 类型）
    trigger_time_start = models.TimeField("开始时间", null=True, blank=True)
    trigger_time_end = models.TimeField("结束时间", null=True, blank=True)
    # 状态条件（可选，用于 TIME_STATE 类型）
    trigger_state_device = models.ForeignKey(
        Device,
        verbose_name="状态设备",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="state_rules",
    )
    trigger_state_value = models.JSONField(
        "状态值", null=True, blank=True, help_text="例如：{\"on\": true}"
    )

    # 执行动作
    action_device = models.ForeignKey(
        Device,
        verbose_name="执行设备",
        on_delete=models.CASCADE,
        related_name="action_rules",
    )
    action_type = models.CharField("动作类型", max_length=32, choices=ACTION_CHOICES)
    action_value = models.JSONField(
        "动作值",
        null=True,
        blank=True,
        help_text="例如：温度值（数字）或风扇档位（1/2/3）",
    )

    # 防抖：避免频繁触发（秒）
    debounce_seconds = models.IntegerField("防抖时间（秒）", default=60)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_triggered_at = models.DateTimeField("最后触发时间", null=True, blank=True)

    class Meta:
        verbose_name = "场景规则"
        verbose_name_plural = "场景规则"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"
