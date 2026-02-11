from django.contrib.auth import get_user_model
from django.test import TestCase

from devices.constants import DeviceType
from devices.models import Device
from scenes.models import SceneRule
from scenes.serializers import SceneRuleSerializer


class SceneRuleConflictValidationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="scene_tester",
            password="scene_tester_pwd_123",
        )
        self.trigger_device = Device.objects.create(
            name="客厅温湿度",
            type=DeviceType.TEMPERATURE_HUMIDITY,
            owner=self.user,
            is_public=True,
        )
        self.action_device = Device.objects.create(
            name="客厅空调",
            type=DeviceType.AC_SWITCH,
            owner=self.user,
            is_public=True,
            current_state={"on": False, "temp": 26},
        )

    def _create_rule(self, **kwargs):
        defaults = {
            "name": "默认规则",
            "owner": self.user,
            "trigger_type": SceneRule.TRIGGER_THRESHOLD_ABOVE,
            "trigger_device": self.trigger_device,
            "trigger_field": "temp",
            "trigger_value": 30,
            "action_device": self.action_device,
            "action_type": SceneRule.ACTION_TURN_ON,
            "action_value": None,
            "debounce_seconds": 60,
        }
        defaults.update(kwargs)
        return SceneRule.objects.create(**defaults)

    def test_create_should_block_when_conflicts_with_existing_rule(self):
        existing = self._create_rule(name="温度高自动开空调")

        serializer = SceneRuleSerializer(
            data={
                "name": "温度高自动关空调",
                "trigger_type": SceneRule.TRIGGER_THRESHOLD_ABOVE,
                "trigger_device": self.trigger_device.id,
                "trigger_field": "temp",
                "trigger_value": 32,
                "action_device": self.action_device.id,
                "action_type": SceneRule.ACTION_TURN_OFF,
                "action_value": None,
                "debounce_seconds": 60,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn("conflicts", serializer.errors)
        message = str(serializer.errors["non_field_errors"][0])
        self.assertIn(existing.name, message)
        self.assertIn("动作类型", message)

    def test_partial_update_should_not_conflict_with_itself(self):
        rule = self._create_rule(name="温度高自动开空调")

        serializer = SceneRuleSerializer(
            instance=rule,
            data={"name": "温度高自动开空调-重命名"},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_edit_should_block_when_updated_rule_conflicts_with_other_rule(self):
        existing = self._create_rule(name="白天温度高自动开空调")
        editable = self._create_rule(name="备用规则", action_type=SceneRule.ACTION_TURN_ON)

        serializer = SceneRuleSerializer(
            instance=editable,
            data={"action_type": SceneRule.ACTION_TURN_OFF},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        message = str(serializer.errors["non_field_errors"][0])
        self.assertIn(existing.name, message)
        self.assertIn("冲突", message)

    def test_create_should_block_when_trigger_overlaps_and_action_is_same(self):
        existing = self._create_rule(
            name="温度低于24开空调",
            trigger_type=SceneRule.TRIGGER_THRESHOLD_BELOW,
            trigger_value=24,
            action_type=SceneRule.ACTION_TURN_ON,
            action_value=None,
        )

        serializer = SceneRuleSerializer(
            data={
                "name": "温度低于28也开空调",
                "trigger_type": SceneRule.TRIGGER_THRESHOLD_BELOW,
                "trigger_device": self.trigger_device.id,
                "trigger_field": "temp",
                "trigger_value": 28,
                "action_device": self.action_device.id,
                "action_type": SceneRule.ACTION_TURN_ON,
                "action_value": None,
                "debounce_seconds": 60,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("conflicts", serializer.errors)
        message = str(serializer.errors["non_field_errors"][0])
        self.assertIn(existing.name, message)
        self.assertIn("重复规则", message)
