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

from django.db import models

# Create your models here.
