from rest_framework import serializers

from .models import EmailAlertRule, SystemLog


class SystemLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemLog
        fields = [
            "id",
            "level",
            "source",
            "message",
            "data",
            "user",
            "created_at",
        ]
        read_only_fields = fields


class EmailAlertRuleSerializer(serializers.ModelSerializer):
    trigger_device_name = serializers.CharField(
        source="trigger_device.name", read_only=True
    )

    class Meta:
        model = EmailAlertRule
        fields = [
            "id",
            "name",
            "enabled",
            "preset",
            "trigger_device",
            "trigger_device_name",
            "trigger_field",
            "trigger_value",
            "trigger_above",
            "recipients",
            "cc_list",
            "subject_template",
            "body_template",
            "last_triggered_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_triggered_at", "created_at", "updated_at"]

