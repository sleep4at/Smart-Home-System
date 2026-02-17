from datetime import datetime

from django.conf import settings
from django.test import TestCase

from .constants import DeviceType
from .energy import _device_energy_in_range, _monthly_estimate
from .models import Device, DeviceData


class EnergyEstimateRegressionTests(TestCase):
    def test_monthly_estimate_does_not_backfill_with_current_state_without_baseline(self):
        """
        无月初基线点时，不应把当前状态回填到月初，避免电费瞬间虚高。
        """
        now = datetime(2026, 2, 10, 12, 0, 0)
        device = Device.objects.create(
            name="客厅空调",
            type=DeviceType.AC_SWITCH,
            current_state={"on": True, "temp": 26, "power_w": 900.0},
        )

        DeviceData.objects.create(
            device=device,
            timestamp=datetime(2026, 2, 10, 10, 0, 0),
            data={"on": True, "temp": 26, "power_w": 900.0},
        )
        DeviceData.objects.create(
            device=device,
            timestamp=datetime(2026, 2, 10, 11, 0, 0),
            data={"on": False, "temp": 26, "power_w": 0.0},
        )

        monthly = _monthly_estimate([device], now=now)
        self.assertAlmostEqual(monthly["energy_kwh_so_far"], 0.9, places=3)
        expected_cost = round(0.9 * float(settings.ENERGY_PRICE_PER_KWH), 2)
        self.assertEqual(monthly["cost_so_far"], expected_cost)

    def test_monthly_estimate_uses_last_point_before_month_start_as_baseline(self):
        """
        有月初之前基线点时，应从该点延续计算，不受 current_state 新值污染。
        """
        now = datetime(2026, 2, 1, 2, 0, 0)
        device = Device.objects.create(
            name="客厅空调",
            type=DeviceType.AC_SWITCH,
            current_state={"on": False, "temp": 26, "power_w": 0.0},
        )

        DeviceData.objects.create(
            device=device,
            timestamp=datetime(2026, 1, 31, 23, 30, 0),
            data={"on": True, "temp": 26},
        )
        DeviceData.objects.create(
            device=device,
            timestamp=datetime(2026, 2, 1, 1, 0, 0),
            data={"on": False, "temp": 26, "power_w": 0.0},
        )

        monthly = _monthly_estimate([device], now=now)
        self.assertAlmostEqual(monthly["energy_kwh_so_far"], 0.9, places=3)
        expected_cost = round(0.9 * float(settings.ENERGY_PRICE_PER_KWH), 2)
        self.assertEqual(monthly["cost_so_far"], expected_cost)

    def test_monthly_estimate_contains_runtime_hours_for_switch_device(self):
        """
        开关类设备应返回当月运行时长（按 on=true 区间累计）。
        """
        now = datetime(2026, 2, 1, 3, 0, 0)
        device = Device.objects.create(
            name="客厅风扇",
            type=DeviceType.FAN_SWITCH,
            current_state={"on": False, "speed": 1, "power_w": 0.0},
        )
        DeviceData.objects.create(
            device=device,
            timestamp=datetime(2026, 2, 1, 0, 30, 0),
            data={"on": True, "speed": 1, "power_w": 30.0},
        )
        DeviceData.objects.create(
            device=device,
            timestamp=datetime(2026, 2, 1, 2, 0, 0),
            data={"on": False, "speed": 1, "power_w": 0.0},
        )

        monthly = _monthly_estimate([device], now=now)
        runtime_map = monthly["runtime_hours_by_device"]
        self.assertIn(device.id, runtime_map)
        self.assertAlmostEqual(runtime_map[device.id], 1.5, places=2)

    def test_device_energy_should_not_keep_old_power_after_off_state_without_power_field(self):
        """
        当历史点仅上报 {"on": false} 时，不应继承更早的 power_w 到关机区间。
        """
        device = Device.objects.create(
            name="客厅空调",
            type=DeviceType.AC_SWITCH,
            current_state={"on": True, "temp": 26},
        )

        # 区间起点前：处于开启且有测量功率
        DeviceData.objects.create(
            device=device,
            timestamp=datetime(2026, 2, 10, 8, 0, 0),
            data={"on": True, "temp": 26, "power_w": 900.0},
        )
        # 关机点：仅上报 on，不带 power_w（历史上可能出现这种状态点）
        DeviceData.objects.create(
            device=device,
            timestamp=datetime(2026, 2, 10, 9, 0, 0),
            data={"on": False},
        )
        # 再次开机点：仍不带 power_w，按估算功率恢复
        DeviceData.objects.create(
            device=device,
            timestamp=datetime(2026, 2, 10, 11, 0, 0),
            data={"on": True, "temp": 26},
        )

        start = datetime(2026, 2, 10, 8, 30, 0)
        end = datetime(2026, 2, 10, 11, 30, 0)
        result = _device_energy_in_range(device, start, end)

        # 仅应计入 08:30-09:00 与 11:00-11:30 两段开启时长：0.9 kWh
        self.assertAlmostEqual(result["energy_kwh"], 0.9, places=3)

        # 验证关键阶梯点：9:00 掉到 0W，11:00 回到约 900W
        series_map = {ts: p for ts, p in result["series"]}
        self.assertEqual(series_map.get(datetime(2026, 2, 10, 9, 0, 0)), 0.0)
        self.assertEqual(series_map.get(datetime(2026, 2, 10, 11, 0, 0)), 900.0)
