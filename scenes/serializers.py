from datetime import time
from typing import Any

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

    @staticmethod
    def _obj_pk(value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        return getattr(value, "pk", None)

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _extract_threshold_value(cls, trigger_value: Any) -> float | None:
        if isinstance(trigger_value, (int, float)):
            return float(trigger_value)
        if isinstance(trigger_value, dict):
            return cls._to_float(trigger_value.get("value"))
        return None

    @classmethod
    def _build_numeric_intervals(
        cls, trigger_type: str, trigger_value: Any
    ) -> list[tuple[float, float]] | None:
        if trigger_type == SceneRule.TRIGGER_THRESHOLD_ABOVE:
            threshold = cls._extract_threshold_value(trigger_value)
            if threshold is None:
                return None
            return [(threshold, float("inf"))]
        if trigger_type == SceneRule.TRIGGER_THRESHOLD_BELOW:
            threshold = cls._extract_threshold_value(trigger_value)
            if threshold is None:
                return None
            return [(-float("inf"), threshold)]
        if trigger_type == SceneRule.TRIGGER_RANGE_OUT:
            if not isinstance(trigger_value, dict):
                return None
            min_v = cls._to_float(trigger_value.get("min"))
            max_v = cls._to_float(trigger_value.get("max"))
            if min_v is None or max_v is None or min_v >= max_v:
                return None
            return [(-float("inf"), min_v), (max_v, float("inf"))]
        return None

    @staticmethod
    def _intervals_overlap(
        first: list[tuple[float, float]], second: list[tuple[float, float]]
    ) -> bool:
        for a_low, a_high in first:
            for b_low, b_high in second:
                if max(a_low, b_low) < min(a_high, b_high):
                    return True
        return False

    @staticmethod
    def _time_to_minutes(value: time) -> int:
        return value.hour * 60 + value.minute

    @classmethod
    def _build_time_windows(
        cls, start: time | None, end: time | None
    ) -> list[tuple[int, int]]:
        if not start or not end:
            return []
        start_min = cls._time_to_minutes(start)
        end_min = cls._time_to_minutes(end)
        if start_min == end_min:
            # 前端输入相同时间通常表示“全天”，冲突检测按全天处理。
            return [(0, 24 * 60)]
        if start_min < end_min:
            return [(start_min, end_min)]
        # 跨天区间
        return [(start_min, 24 * 60), (0, end_min)]

    @classmethod
    def _time_windows_overlap(
        cls, first: list[tuple[int, int]], second: list[tuple[int, int]]
    ) -> bool:
        return cls._intervals_overlap(
            [(float(a), float(b)) for a, b in first],
            [(float(a), float(b)) for a, b in second],
        )

    @classmethod
    def _state_conditions_overlap(
        cls, first: dict[str, Any] | None, second: dict[str, Any] | None
    ) -> bool:
        if not first or not second:
            return True
        bool_like_keys = {"on", "motion", "pir", "value", "detected", "alarm", "smoke"}
        common_keys = set(first.keys()) & set(second.keys())
        for key in common_keys:
            left = first.get(key)
            right = second.get(key)
            if key in bool_like_keys:
                if bool(left) != bool(right):
                    return False
                continue
            left_num = cls._to_float(left)
            right_num = cls._to_float(right)
            if left_num is not None and right_num is not None:
                if left_num != right_num:
                    return False
                continue
            if left != right:
                return False
        return True

    @classmethod
    def _action_signature(cls, action_type: str, action_value: Any) -> dict[str, Any]:
        signature: dict[str, Any] = {
            "toggle": False,
            "desired_on": None,
            "temp": None,
            "speed": None,
        }
        if action_type == SceneRule.ACTION_TOGGLE:
            signature["toggle"] = True
            return signature
        if action_type == SceneRule.ACTION_TURN_ON:
            signature["desired_on"] = True
            return signature
        if action_type == SceneRule.ACTION_TURN_OFF:
            signature["desired_on"] = False
            return signature
        if action_type == SceneRule.ACTION_SET_TEMP:
            signature["desired_on"] = True
            if isinstance(action_value, dict):
                signature["temp"] = cls._to_float(action_value.get("temp"))
            else:
                signature["temp"] = cls._to_float(action_value)
            return signature
        if action_type == SceneRule.ACTION_SET_FAN_SPEED:
            signature["desired_on"] = True
            if isinstance(action_value, dict):
                speed = cls._to_float(action_value.get("speed"))
            else:
                speed = cls._to_float(action_value)
            signature["speed"] = int(speed) if speed is not None else None
            return signature
        return signature

    @staticmethod
    def _action_desc(action_type: str, action_value: Any) -> str:
        if action_type == SceneRule.ACTION_TOGGLE:
            return "切换开关"
        if action_type == SceneRule.ACTION_TURN_ON:
            return "开启设备"
        if action_type == SceneRule.ACTION_TURN_OFF:
            return "关闭设备"
        if action_type == SceneRule.ACTION_SET_TEMP:
            if isinstance(action_value, dict):
                temp = action_value.get("temp")
            else:
                temp = action_value
            return f"设置温度 {temp}°C"
        if action_type == SceneRule.ACTION_SET_FAN_SPEED:
            if isinstance(action_value, dict):
                speed = action_value.get("speed")
            else:
                speed = action_value
            return f"设置风扇档位 {speed}"
        return action_type

    def _effective_value(self, attrs: dict[str, Any], field: str, default: Any = None) -> Any:
        if field in attrs:
            return attrs.get(field)
        if self.instance is not None:
            return getattr(self.instance, field)
        return default

    def _trigger_overlap(self, candidate: dict[str, Any], existing: SceneRule) -> bool:
        if candidate["trigger_device_id"] != existing.trigger_device_id:
            return False

        candidate_type = candidate["trigger_type"]
        existing_type = existing.trigger_type

        if candidate_type == SceneRule.TRIGGER_TIME_STATE or existing_type == SceneRule.TRIGGER_TIME_STATE:
            if candidate_type != SceneRule.TRIGGER_TIME_STATE or existing_type != SceneRule.TRIGGER_TIME_STATE:
                return False
            candidate_windows = self._build_time_windows(
                candidate["trigger_time_start"], candidate["trigger_time_end"]
            )
            existing_windows = self._build_time_windows(
                existing.trigger_time_start, existing.trigger_time_end
            )
            if not candidate_windows or not existing_windows:
                return False
            if not self._time_windows_overlap(candidate_windows, existing_windows):
                return False

            candidate_state_device_id = candidate["trigger_state_device_id"]
            existing_state_device_id = existing.trigger_state_device_id
            if (
                candidate_state_device_id
                and existing_state_device_id
                and candidate_state_device_id != existing_state_device_id
            ):
                return False

            return self._state_conditions_overlap(
                candidate["trigger_state_value"], existing.trigger_state_value
            )

        if candidate["trigger_field"] != existing.trigger_field:
            return False
        candidate_intervals = self._build_numeric_intervals(
            candidate_type, candidate["trigger_value"]
        )
        existing_intervals = self._build_numeric_intervals(
            existing_type, existing.trigger_value
        )
        if not candidate_intervals or not existing_intervals:
            return False
        return self._intervals_overlap(candidate_intervals, existing_intervals)

    def _action_conflict(
        self, candidate: dict[str, Any], existing: SceneRule
    ) -> tuple[str, str] | None:
        if candidate["action_device_id"] != existing.action_device_id:
            return None

        candidate_action = self._action_signature(
            candidate["action_type"], candidate["action_value"]
        )
        existing_action = self._action_signature(existing.action_type, existing.action_value)

        if candidate_action["toggle"] and existing_action["toggle"]:
            return ("action_type", "两个规则都使用“切换开关”，同条件下会产生来回切换")
        if candidate_action["toggle"] or existing_action["toggle"]:
            return ("action_type", "包含“切换开关”动作，可能与其他动作互相抵消")

        # 同一触发区间内执行完全一致的动作，属于重复规则，也应阻止保存。
        if (
            candidate_action["desired_on"] == existing_action["desired_on"]
            and candidate_action["temp"] == existing_action["temp"]
            and candidate_action["speed"] == existing_action["speed"]
        ):
            return ("trigger_value", "触发条件重叠且执行动作一致，属于重复规则")

        candidate_on = candidate_action["desired_on"]
        existing_on = existing_action["desired_on"]
        if (
            candidate_on is not None
            and existing_on is not None
            and bool(candidate_on) != bool(existing_on)
        ):
            return ("action_type", "一个要求开启，另一个要求关闭")

        candidate_sets_param = (
            candidate_action["temp"] is not None or candidate_action["speed"] is not None
        )
        existing_sets_param = (
            existing_action["temp"] is not None or existing_action["speed"] is not None
        )
        if (candidate_on is False and existing_sets_param) or (
            existing_on is False and candidate_sets_param
        ):
            return ("action_type", "一个要求关闭，另一个要求设置参数并开启")

        if (
            candidate_action["temp"] is not None
            and existing_action["temp"] is not None
            and float(candidate_action["temp"]) != float(existing_action["temp"])
        ):
            return (
                "action_value",
                f"目标温度不同（{candidate_action['temp']}°C vs {existing_action['temp']}°C）",
            )

        if (
            candidate_action["speed"] is not None
            and existing_action["speed"] is not None
            and int(candidate_action["speed"]) != int(existing_action["speed"])
        ):
            return (
                "action_value",
                f"风扇档位不同（{candidate_action['speed']} vs {existing_action['speed']}）",
            )

        return None

    def _find_conflicts(self, candidate: dict[str, Any]) -> list[dict[str, Any]]:
        queryset = SceneRule.objects.select_related("action_device", "trigger_device")
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        conflicts: list[dict[str, Any]] = []
        for existing in queryset:
            if not self._trigger_overlap(candidate, existing):
                continue
            action_conflict = self._action_conflict(candidate, existing)
            if not action_conflict:
                continue

            conflict_field, reason = action_conflict
            if conflict_field == "action_type":
                conflict_field_label = "动作类型"
            elif conflict_field == "action_value":
                conflict_field_label = "动作值"
            elif conflict_field == "trigger_value":
                conflict_field_label = "触发条件"
            else:
                conflict_field_label = "规则项"
            action_device_name = getattr(candidate["action_device"], "name", f"设备#{candidate['action_device_id']}")
            if conflict_field == "trigger_value":
                message = (
                    f"与规则「{existing.name}」冲突：{conflict_field_label}冲突（{reason}）。"
                    f"执行设备「{action_device_name}」的动作一致："
                    f"{self._action_desc(candidate['action_type'], candidate['action_value'])}。"
                )
            else:
                message = (
                    f"与规则「{existing.name}」冲突：在相同触发条件下，执行设备「{action_device_name}」"
                    f"的{conflict_field_label}冲突（{reason}）。"
                    f"本规则动作：{self._action_desc(candidate['action_type'], candidate['action_value'])}；"
                    f"冲突规则动作：{self._action_desc(existing.action_type, existing.action_value)}。"
                )
            conflicts.append(
                {
                    "rule_id": existing.id,
                    "rule_name": existing.name,
                    "conflict_field": conflict_field,
                    "conflict_field_label": conflict_field_label,
                    "action_device_id": existing.action_device_id,
                    "action_device_name": existing.action_device.name,
                    "message": message,
                }
            )
        return conflicts

    def validate(self, attrs):
        """验证规则逻辑的合理性。"""
        trigger_type = self._effective_value(attrs, "trigger_type")
        trigger_value = self._effective_value(attrs, "trigger_value")
        trigger_device = self._effective_value(attrs, "trigger_device")
        action_device = self._effective_value(attrs, "action_device")
        trigger_field = self._effective_value(attrs, "trigger_field")
        trigger_time_start = self._effective_value(attrs, "trigger_time_start")
        trigger_time_end = self._effective_value(attrs, "trigger_time_end")
        trigger_state_device = self._effective_value(attrs, "trigger_state_device")
        trigger_state_value = self._effective_value(attrs, "trigger_state_value")
        action_type = self._effective_value(attrs, "action_type")
        action_value = self._effective_value(attrs, "action_value")

        # 创建时传入的可能是 pk (int)，0 表示未选择
        tpk = self._obj_pk(trigger_device)
        if tpk is None or tpk == 0:
            raise serializers.ValidationError({"trigger_device": "请选择触发设备。"})
        apk = self._obj_pk(action_device)
        if apk is None or apk == 0:
            raise serializers.ValidationError({"action_device": "请选择执行设备。"})

        if trigger_type == SceneRule.TRIGGER_RANGE_OUT:
            if not isinstance(trigger_value, dict) or "min" not in trigger_value or "max" not in trigger_value:
                raise serializers.ValidationError(
                    {"trigger_value": "区间触发类型需要 trigger_value 为 {\"min\": X, \"max\": Y} 格式"}
                )
            if trigger_value["min"] >= trigger_value["max"]:
                raise serializers.ValidationError({"trigger_value": "最小值必须小于最大值"})
        elif trigger_type in (SceneRule.TRIGGER_THRESHOLD_ABOVE, SceneRule.TRIGGER_THRESHOLD_BELOW):
            threshold = self._extract_threshold_value(trigger_value)
            if threshold is None:
                raise serializers.ValidationError({"trigger_value": "阈值触发类型需要 trigger_value 为数字。"})

        if trigger_type == SceneRule.TRIGGER_TIME_STATE:
            if not trigger_time_start or not trigger_time_end:
                raise serializers.ValidationError(
                    {"trigger_time_start": "时间+状态组合触发需要设置开始和结束时间"}
                )
        elif not trigger_field:
            raise serializers.ValidationError({"trigger_field": "请选择触发字段。"})

        candidate = {
            "trigger_type": trigger_type,
            "trigger_device": trigger_device,
            "trigger_device_id": tpk,
            "trigger_field": trigger_field,
            "trigger_value": trigger_value,
            "trigger_time_start": trigger_time_start,
            "trigger_time_end": trigger_time_end,
            "trigger_state_device": trigger_state_device,
            "trigger_state_device_id": self._obj_pk(trigger_state_device),
            "trigger_state_value": trigger_state_value if isinstance(trigger_state_value, dict) else None,
            "action_device": action_device,
            "action_device_id": apk,
            "action_type": action_type,
            "action_value": action_value,
        }

        conflicts = self._find_conflicts(candidate)
        if conflicts:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [item["message"] for item in conflicts],
                    "conflicts": conflicts,
                }
            )

        return attrs
