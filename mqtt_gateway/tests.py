from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from devices.constants import DeviceType
from devices.models import Device
from logs_app.models import SystemLog
from mqtt_gateway.management.commands.run_mqtt_gateway import Command
from scenes.models import SceneRule


class SceneRuleExecutionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="scene_user",
            password="pass123456",
        )
        self.trigger_device = Device.objects.create(
            name="温度传感器",
            type=DeviceType.TEMPERATURE_HUMIDITY,
            owner=self.user,
            is_online=True,
            current_state={"temp": 25.0},
        )
        self.action_device = Device.objects.create(
            name="客厅空调",
            type=DeviceType.AC_SWITCH,
            owner=self.user,
            is_online=False,
            current_state={"on": False},
        )
        self.rule = SceneRule.objects.create(
            name="高温开空调",
            enabled=True,
            owner=self.user,
            trigger_type=SceneRule.TRIGGER_THRESHOLD_ABOVE,
            trigger_device=self.trigger_device,
            trigger_field="temp",
            trigger_value=28.0,
            action_device=self.action_device,
            action_type=SceneRule.ACTION_TURN_ON,
            action_value={},
            debounce_seconds=0,
        )
        self.command = Command()

    def test_skip_scene_rule_when_action_device_offline(self):
        with patch("mqtt_gateway.utils.publish_device_command") as publish_mock:
            self.command._check_and_execute_scene_rules(
                self.trigger_device,
                {"temp": 30.5},
            )

        self.action_device.refresh_from_db()
        self.rule.refresh_from_db()

        self.assertFalse(self.action_device.current_state.get("on", False))
        self.assertIsNone(self.rule.last_triggered_at)
        publish_mock.assert_not_called()
        self.assertFalse(
            SystemLog.objects.filter(source="SCENE_RULE", data__rule_id=self.rule.id).exists()
        )

    def test_execute_scene_rule_when_action_device_online(self):
        self.action_device.is_online = True
        self.action_device.save(update_fields=["is_online"])

        with patch("mqtt_gateway.utils.publish_device_command") as publish_mock:
            self.command._check_and_execute_scene_rules(
                self.trigger_device,
                {"temp": 30.5},
            )

        self.action_device.refresh_from_db()
        self.rule.refresh_from_db()

        self.assertTrue(self.action_device.current_state.get("on"))
        self.assertIsNotNone(self.rule.last_triggered_at)
        publish_mock.assert_called_once_with(
            device_id=self.action_device.id,
            payload={"on": True},
        )
        self.assertTrue(
            SystemLog.objects.filter(source="SCENE_RULE", data__rule_id=self.rule.id).exists()
        )
