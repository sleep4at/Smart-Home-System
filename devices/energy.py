from __future__ import annotations

import calendar
from datetime import timedelta
from typing import Iterable

from django.conf import settings
from django.utils import timezone

from .constants import DeviceType
from .models import Device, DeviceData


RANGE_TO_DELTA = {
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "3d": timedelta(days=3),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

RUNTIME_TRACKABLE_TYPES = {
    DeviceType.LAMP_SWITCH,
    DeviceType.FAN_SWITCH,
    DeviceType.AC_SWITCH,
}


def _to_float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _profile() -> dict:
    return getattr(settings, "ENERGY_POWER_PROFILE", {})


def _is_runtime_trackable(device: Device) -> bool:
    return device.type in RUNTIME_TRACKABLE_TYPES


def _is_device_running(device: Device, state: dict | None, power_w: float) -> bool:
    if not _is_runtime_trackable(device):
        return False
    if isinstance(state, dict) and "on" in state:
        return bool(state.get("on"))
    return float(power_w) > 0.0


def _extract_measured_power_w(state: dict | None) -> float | None:
    if not isinstance(state, dict):
        return None
    value = state.get("power_w", state.get("power"))
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def estimate_power_w(device: Device, state: dict | None) -> float:
    """
    根据设备类型和状态估算当前功率（W）。
    """
    s = state if isinstance(state, dict) else {}
    p = _profile()
    on = bool(s.get("on"))

    if device.type == DeviceType.LAMP_SWITCH:
        return p.get("LAMP_ON_W", 9.0) if on else 0.0

    if device.type == DeviceType.FAN_SWITCH:
        if not on:
            return 0.0
        speed = int(_to_float(s.get("speed"), 1.0))
        if speed <= 1:
            return p.get("FAN_SPEED_1_W", 30.0)
        if speed == 2:
            return p.get("FAN_SPEED_2_W", 45.0)
        return p.get("FAN_SPEED_3_W", 60.0)

    if device.type == DeviceType.AC_SWITCH:
        if not on:
            return 0.0
        temp = _to_float(s.get("temp"), 26.0)
        base = p.get("AC_BASE_W", 900.0)
        step = p.get("AC_TEMP_STEP_W", 25.0)
        min_w = p.get("AC_MIN_W", 500.0)
        max_w = p.get("AC_MAX_W", 1500.0)
        estimated = base + (26.0 - temp) * step
        return max(min_w, min(max_w, estimated))

    if device.type in (
        DeviceType.TEMPERATURE_HUMIDITY,
        DeviceType.LIGHT,
        DeviceType.PRESSURE,
        DeviceType.PIR,
        DeviceType.SMOKE,
    ):
        # 传感器默认按待机功耗估算；若无状态点则按 0W。
        return p.get("SENSOR_IDLE_W", 0.5) if s else 0.0

    return 0.0


def _get_time_range(range_value: str, now=None):
    now = now or timezone.now()
    delta = RANGE_TO_DELTA.get(range_value, RANGE_TO_DELTA["24h"])
    return now - delta, now


def _device_energy_in_range(device: Device, start, end):
    """
    计算单设备在 [start, end] 的功率阶梯线和能耗。
    """
    prev = (
        DeviceData.objects.filter(device=device, timestamp__lt=start)
        .order_by("-timestamp")
        .values("timestamp", "data")
        .first()
    )

    prev_data = (prev or {}).get("data") or {}
    if isinstance(prev_data, dict):
        # 仅使用区间起点之前最后一条历史点作为基线，避免把“当前状态”回填到过去。
        current_state = prev_data.copy()
        # 历史点可能是 {"on": false}（未携带 power_w），
        # 此时不能继承更早的测量功率到关机区间。
        if "on" in current_state and not bool(current_state.get("on")):
            current_state.pop("power_w", None)
            current_state.pop("power", None)
        measured = _extract_measured_power_w(current_state)
        current_power = measured if measured is not None else estimate_power_w(device, current_state)
    else:
        # 若没有历史基线，起点按 0W 处理，直到首条区间内历史点到来。
        current_state = {}
        current_power = 0.0

    points = list(
        DeviceData.objects.filter(device=device, timestamp__gte=start, timestamp__lte=end)
        .order_by("timestamp")
        .values("timestamp", "data")
    )

    series = [(start, float(current_power))]
    energy_kwh = 0.0
    runtime_hours = 0.0
    runtime_trackable = _is_runtime_trackable(device)
    cursor = start

    for row in points:
        ts = row["timestamp"]
        row_data = row.get("data") or {}
        if ts <= cursor:
            next_state = current_state.copy()
            if isinstance(row_data, dict):
                next_state.update(row_data)
                # 同上：当该条仅表示关机（未给 power 字段）时，清理旧功率，避免“关机后仍高功率”。
                if "on" in row_data and "power_w" not in row_data and "power" not in row_data:
                    if not bool(row_data.get("on")):
                        next_state.pop("power_w", None)
                        next_state.pop("power", None)
            current_state = next_state
            measured = _extract_measured_power_w(current_state)
            current_power = measured if measured is not None else estimate_power_w(device, current_state)
            continue

        duration_hours = (ts - cursor).total_seconds() / 3600.0
        energy_kwh += float(current_power) * duration_hours / 1000.0
        if runtime_trackable and _is_device_running(device, current_state, float(current_power)):
            runtime_hours += duration_hours

        new_state = current_state.copy()
        if isinstance(row_data, dict):
            new_state.update(row_data)
            # 同上：当该条仅表示关机（未给 power 字段）时，清理旧功率，避免“关机后仍高功率”。
            if "on" in row_data and "power_w" not in row_data and "power" not in row_data:
                if not bool(row_data.get("on")):
                    new_state.pop("power_w", None)
                    new_state.pop("power", None)
        measured = _extract_measured_power_w(new_state)
        new_power = measured if measured is not None else estimate_power_w(device, new_state)
        if float(new_power) != float(current_power):
            series.append((ts, float(new_power)))
        current_state = new_state
        current_power = new_power
        cursor = ts

    if end > cursor:
        duration_hours = (end - cursor).total_seconds() / 3600.0
        energy_kwh += float(current_power) * duration_hours / 1000.0
        if runtime_trackable and _is_device_running(device, current_state, float(current_power)):
            runtime_hours += duration_hours

    if series[-1][0] != end:
        series.append((end, float(current_power)))

    peak_w = max((p for _, p in series), default=0.0)
    total_hours = max((end - start).total_seconds() / 3600.0, 1e-6)
    avg_w = energy_kwh * 1000.0 / total_hours
    price = float(getattr(settings, "ENERGY_PRICE_PER_KWH", 0.56))

    return {
        "device": device,
        "series": series,
        "energy_kwh": energy_kwh,
        "peak_power_w": peak_w,
        "avg_power_w": avg_w,
        "cost": energy_kwh * price,
        "runtime_hours": runtime_hours,
        "runtime_trackable": runtime_trackable,
    }


def _aggregate_devices(device_results: list[dict], start, end):
    if not device_results:
        return {
            "series": [(start, 0.0), (end, 0.0)],
            "energy_kwh": 0.0,
            "peak_power_w": 0.0,
            "avg_power_w": 0.0,
            "cost": 0.0,
        }

    initial_total = sum((r["series"][0][1] if r["series"] else 0.0) for r in device_results)
    events = {}
    for result in device_results:
        series = result["series"]
        for i in range(1, len(series)):
            prev_ts, prev_power = series[i - 1]
            ts, power = series[i]
            if ts < start or ts > end:
                continue
            delta = float(power) - float(prev_power)
            if delta == 0:
                continue
            events[ts] = events.get(ts, 0.0) + delta

    total_series = [(start, float(initial_total))]
    current_total = float(initial_total)
    for ts in sorted(events.keys()):
        if ts <= start or ts > end:
            continue
        current_total += float(events[ts])
        total_series.append((ts, current_total))
    if total_series[-1][0] != end:
        total_series.append((end, current_total))

    total_energy = sum(float(r["energy_kwh"]) for r in device_results)
    total_peak = max((p for _, p in total_series), default=0.0)
    total_hours = max((end - start).total_seconds() / 3600.0, 1e-6)
    total_avg = total_energy * 1000.0 / total_hours
    price = float(getattr(settings, "ENERGY_PRICE_PER_KWH", 0.56))

    return {
        "series": total_series,
        "energy_kwh": total_energy,
        "peak_power_w": total_peak,
        "avg_power_w": total_avg,
        "cost": total_energy * price,
    }


def _monthly_estimate(devices: list[Device], now=None):
    now = now or timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    month_end = month_start + timedelta(days=days_in_month)

    device_results = [_device_energy_in_range(d, month_start, now) for d in devices]
    summary = _aggregate_devices(device_results, month_start, now)
    runtime_hours_by_device: dict[int, float] = {}
    for result in device_results:
        if result.get("runtime_trackable"):
            runtime_hours_by_device[result["device"].id] = round(
                float(result.get("runtime_hours", 0.0)), 2
            )

    elapsed_seconds = max((now - month_start).total_seconds(), 1.0)
    month_seconds = max((month_end - month_start).total_seconds(), 1.0)
    projected_energy = summary["energy_kwh"] / elapsed_seconds * month_seconds
    price = float(getattr(settings, "ENERGY_PRICE_PER_KWH", 0.56))

    return {
        "month": f"{now.year:04d}-{now.month:02d}",
        "energy_kwh_so_far": round(summary["energy_kwh"], 3),
        "cost_so_far": round(summary["cost"], 2),
        "projected_energy_kwh": round(projected_energy, 3),
        "projected_cost": round(projected_energy * price, 2),
        "elapsed_days": round(elapsed_seconds / 86400.0, 2),
        "days_in_month": days_in_month,
        "runtime_hours_by_device": runtime_hours_by_device,
    }


def build_energy_analysis(devices: Iterable[Device], range_value: str, now=None):
    """
    生成能耗分析响应数据（单设备或多设备）。
    """
    devices = list(devices)
    now = now or timezone.now()
    start, end = _get_time_range(range_value, now=now)

    device_results = [_device_energy_in_range(device, start, end) for device in devices]
    total = _aggregate_devices(device_results, start, end)

    price = float(getattr(settings, "ENERGY_PRICE_PER_KWH", 0.56))
    monthly = _monthly_estimate(devices, now=now)
    monthly_runtime = monthly.get("runtime_hours_by_device", {})

    device_breakdown = []
    for result in device_results:
        device = result["device"]
        device_breakdown.append(
            {
                "device_id": device.id,
                "name": device.name,
                "location": device.location,
                "type": device.type,
                "type_display": device.get_type_display(),
                "energy_kwh": round(result["energy_kwh"], 3),
                "cost": round(result["cost"], 2),
                "peak_power_w": round(result["peak_power_w"], 1),
                "avg_power_w": round(result["avg_power_w"], 1),
                "monthly_runtime_hours": monthly_runtime.get(device.id),
            }
        )
    device_breakdown.sort(key=lambda x: x["energy_kwh"], reverse=True)

    series = [
        {
            "timestamp": ts.isoformat(),
            "power_w": round(power, 1),
        }
        for ts, power in total["series"]
    ]

    return {
        "range": range_value,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "price_per_kwh": price,
        "total": {
            "energy_kwh": round(total["energy_kwh"], 3),
            "cost": round(total["cost"], 2),
            "peak_power_w": round(total["peak_power_w"], 1),
            "avg_power_w": round(total["avg_power_w"], 1),
        },
        "series": series,
        "device_breakdown": device_breakdown,
        "monthly_estimate": monthly,
    }
