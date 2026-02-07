from django.conf import settings
from django.db import models


class SystemLog(models.Model):
    """
    系统/调试日志，用于“调试信息”页面展示。
    """

    LEVEL_INFO = "INFO"
    LEVEL_WARN = "WARN"
    LEVEL_ERROR = "ERROR"

    LEVEL_CHOICES = (
        (LEVEL_INFO, "信息"),
        (LEVEL_WARN, "警告"),
        (LEVEL_ERROR, "错误"),
    )

    level = models.CharField("级别", max_length=10, choices=LEVEL_CHOICES, default=LEVEL_INFO)
    source = models.CharField("来源", max_length=50, default="SYSTEM")
    message = models.TextField("消息")
    data = models.JSONField("附加数据", null=True, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="相关用户",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "系统日志"
        verbose_name_plural = "系统日志"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.level}] {self.source}: {self.message[:40]}"


class EmailAlertRule(models.Model):
    """
    邮件告警规则：当触发设备满足条件时，向指定邮箱发送告警邮件。
    """

    PRESET_TEMP_HIGH = "temp_high"
    PRESET_TEMP_LOW = "temp_low"
    PRESET_HUMI_HIGH = "humi_high"
    PRESET_HUMI_LOW = "humi_low"
    PRESET_SMOKE = "smoke"
    PRESET_CUSTOM = "custom"

    PRESET_CHOICES = (
        (PRESET_TEMP_HIGH, "温度过高"),
        (PRESET_TEMP_LOW, "温度过低"),
        (PRESET_HUMI_HIGH, "湿度过高"),
        (PRESET_HUMI_LOW, "湿度过低"),
        (PRESET_SMOKE, "烟雾告警"),
        (PRESET_CUSTOM, "自定义"),
    )

    name = models.CharField("规则名称", max_length=100)
    enabled = models.BooleanField("是否启用", default=True)
    preset = models.CharField(
        "预设类型", max_length=32, choices=PRESET_CHOICES, default=PRESET_TEMP_HIGH
    )

    trigger_device = models.ForeignKey(
        "devices.Device",
        verbose_name="触发设备",
        on_delete=models.CASCADE,
        related_name="email_alert_rules",
    )
    trigger_field = models.CharField(
        "触发字段", max_length=32, default="temp", help_text="temp / humi / smoke 等"
    )
    trigger_value = models.FloatField(
        "触发阈值", help_text="超过或低于此值即触发", null=True, blank=True
    )
    trigger_above = models.BooleanField(
        "高于阈值触发", default=True, help_text="True=高于触发，False=低于触发"
    )

    recipients = models.JSONField(
        "收件邮箱列表",
        default=list,
        help_text='["admin@example.com", "user@example.com"]',
    )
    cc_list = models.JSONField("抄送列表", default=list, blank=True)
    subject_template = models.CharField(
        "邮件主题", max_length=200, default="[智能家居告警] {preset} - {device_name}"
    )
    body_template = models.TextField(
        "邮件正文模板",
        default="触发设备：{device_name}\n触发条件：{preset}\n当前值：{value}\n时间：{time}",
    )

    last_triggered_at = models.DateTimeField("最后触发时间", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "邮件告警规则"
        verbose_name_plural = "邮件告警规则"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_preset_display()})"
