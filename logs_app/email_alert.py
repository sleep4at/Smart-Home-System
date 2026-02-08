"""
邮件告警发送：根据规则向收件人发送告警邮件。
"""
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailAlertRule, SystemLog


def send_email_alerts_for_value(device, field: str, value: float):
    """
    当设备上报的某字段值触发某条邮件规则时，发送邮件。
    field: "temp" / "humi" / "smoke" 等
    value: 当前数值（烟雾为 1.0=触发 / 0.0=未触发）
    """
    rules = EmailAlertRule.objects.filter(
        enabled=True,
        trigger_device=device,
        trigger_field=field,
    ).select_related("trigger_device")

    # 仅当烟雾实际触发（value >= 1）且没有匹配规则时再记录日志，避免未触发时误报
    if field == "smoke" and not rules.exists():
        if value >= 1.0:
            SystemLog.objects.create(
                level=SystemLog.LEVEL_INFO,
                source="EMAIL_ALERT",
                message=f"烟雾设备 [{device.name}] 触发告警，但未找到匹配的邮件告警规则（触发设备 ID={device.id}，trigger_field=smoke）",
                data={"device_id": device.id, "device_name": device.name, "value": value},
            )
        return

    for rule in rules:
        # 烟雾告警：trigger_value 可为 None，视为 1（触发即发邮件）
        threshold = rule.trigger_value
        if threshold is None and field != "smoke":
            continue
        if field == "smoke" and threshold is None:
            threshold = 1.0
        triggered = False
        if rule.trigger_above:
            triggered = value >= threshold
        else:
            triggered = value <= threshold

        if not triggered:
            continue

        if not rule.recipients:
            SystemLog.objects.create(
                level=SystemLog.LEVEL_WARN,
                source="EMAIL_ALERT",
                message=f"告警规则「{rule.name}」未配置收件人，跳过发送",
                data={"rule_id": rule.id},
            )
            continue

        try:
            subject = rule.subject_template.format(
                preset=rule.get_preset_display(),
                device_name=device.name,
                value=value,
                time=timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        except KeyError:
            subject = f"[告警] {rule.get_preset_display()} - {device.name}"

        try:
            body = rule.body_template.format(
                preset=rule.get_preset_display(),
                device_name=device.name,
                value=value,
                time=timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        except KeyError:
            body = f"触发设备：{device.name}\n触发条件：{rule.get_preset_display()}\n当前值：{value}\n时间：{timezone.now()}"

        try:
            send_mail(
                subject=subject[:200],
                message=body,
                from_email=None,
                recipient_list=rule.recipients,
                # fail_silently=True,
                fail_silently=False,
                html_message=None,
            )
            rule.last_triggered_at = timezone.now()
            rule.save(update_fields=["last_triggered_at"])
            msg = f"告警邮件已发送：{rule.name} -> {', '.join(rule.recipients[:3])}{'...' if len(rule.recipients) > 3 else ''}"
            SystemLog.objects.create(
                level=SystemLog.LEVEL_INFO,
                source="EMAIL_ALERT",
                message=msg,
                data={"rule_id": rule.id, "device_name": device.name, "value": value},
            )
        except Exception as e:
            SystemLog.objects.create(
                level=SystemLog.LEVEL_ERROR,
                source="EMAIL_ALERT",
                message=f"告警邮件发送失败：{rule.name} - {e}",
                data={"rule_id": rule.id},
            )
