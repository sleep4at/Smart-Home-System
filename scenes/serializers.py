from rest_framework import serializers

from devices.serializers import DeviceSerializer
from .models import SceneRule


class SceneRuleSerializer(serializers.ModelSerializer):
    """
    场景规则序列化器。
    """

    trigger_device_detail = DeviceSerializer(source="trigger_device", read_only=True)
    action_device_detail = DeviceSerializer(source="action_device", read_only=True)
    trigger_state_device_detail = DeviceSerializer(
        source="trigger_state_device", read_only=True
    )
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = SceneRule
        fields = [
            "id",
            "name",
            "enabled",
            "owner",
            "owner_username",
            "trigger_type",
            "trigger_device",
            "trigger_device_detail",
            "trigger_field",
            "trigger_value",
            "trigger_time_start",
            "trigger_time_end",
            "trigger_state_device",
            "trigger_state_device_detail",
            "trigger_state_value",
            "action_device",
            "action_device_detail",
            "action_type",
            "action_value",
            "debounce_seconds",
            "created_at",
            "updated_at",
            "last_triggered_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at", "last_triggered_at"]

    def validate(self, attrs):
        """验证规则逻辑的合理性。"""
        trigger_type = attrs.get("trigger_type")
        trigger_value = attrs.get("trigger_value")
        trigger_device = attrs.get("trigger_device")
        action_device = attrs.get("action_device")

        # 创建时传入的可能是 pk (int)，0 表示未选择
        tpk = trigger_device if isinstance(trigger_device, int) else getattr(trigger_device, "pk", None)
        if tpk is None or tpk == 0:
            raise serializers.ValidationError({"trigger_device": "请选择触发设备。"})
        apk = action_device if isinstance(action_device, int) else getattr(action_device, "pk", None)
        if apk is None or apk == 0:
            raise serializers.ValidationError({"action_device": "请选择执行设备。"})

        if trigger_type == SceneRule.TRIGGER_RANGE_OUT:
            if not isinstance(trigger_value, dict) or "min" not in trigger_value or "max" not in trigger_value:
                raise serializers.ValidationError(
                    {"trigger_value": "区间触发类型需要 trigger_value 为 {\"min\": X, \"max\": Y} 格式"}
                )
            if trigger_value["min"] >= trigger_value["max"]:
                raise serializers.ValidationError({"trigger_value": "最小值必须小于最大值"})

        if trigger_type == SceneRule.TRIGGER_TIME_STATE:
            if not attrs.get("trigger_time_start") or not attrs.get("trigger_time_end"):
                raise serializers.ValidationError(
                    {"trigger_time_start": "时间+状态组合触发需要设置开始和结束时间"}
                )

        return attrs
