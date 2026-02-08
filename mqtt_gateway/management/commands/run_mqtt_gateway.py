"""
运行 MQTT 网关：订阅 home/+/state，更新设备状态与历史数据。
用法：python3 manage.py run_mqtt_gateway
"""

import json

import paho.mqtt.client as mqtt
from django.conf import settings
from django.core.mail import mail_admins

from logs_app.email_alert import send_email_alerts_for_value
from django.core.management.base import BaseCommand
from django.utils import timezone

from devices.constants import DeviceType
from devices.models import Device, DeviceData
from logs_app.models import SystemLog
from scenes.models import SceneRule


class Command(BaseCommand):
    help = "运行 MQTT 网关，订阅设备状态并更新数据库"

    def handle(self, *args, **options):
        config = settings.MQTT_CONFIG
        topic_prefix = config.get("TOPIC_PREFIX", "home")

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.stdout.write(
                    self.style.SUCCESS(f"MQTT 已连接: {config['HOST']}:{config['PORT']}")
                )
                # 设备状态上报
                client.subscribe(f"{topic_prefix}/+/state", qos=1)
                # LWT / 在线状态主题（约定为 lwt，可按需调整）
                client.subscribe(f"{topic_prefix}/+/lwt", qos=1)
                self.stdout.write(f"已订阅: {topic_prefix}/+/state, {topic_prefix}/+/lwt")
            else:
                self.stdout.write(self.style.ERROR(f"MQTT 连接失败 rc={rc}"))

                
        # ChatGPT 优化后的代码
        def on_message(client, userdata, msg):
            try:
                # 1. 打印原始收到的消息（最关键的排查点）
                topic = msg.topic
                raw_payload = msg.payload.decode()
                self.stdout.write(f"收到消息 -> 主题: {topic} | 内容: {raw_payload}")

                # 解析 Topic 结构 (期望格式: home/{id}/{suffix})
                parts = topic.split("/")
                if len(parts) < 3:
                    self.stdout.write(self.style.WARNING(f"主题格式错误: 期望 3 段，实际 {len(parts)} 段"))
                    return

                # 提取设备 ID
                try:
                    # 假设格式是 prefix/id/xxx
                    device_id = int(parts[1])
                except (ValueError, IndexError):
                    self.stdout.write(self.style.WARNING(f"无法从主题中提取数字 ID: {parts[1]}"))
                    return

                suffix = parts[2]

                # 查找设备
                try:
                    device = Device.objects.get(pk=device_id)
                except Device.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"数据库中不存在 ID 为 {device_id} 的设备"))
                    return

                # 2. 解析 JSON（state 和 lwt 都优先尝试 JSON）
                try:
                    payload = json.loads(raw_payload)
                except json.JSONDecodeError:
                    payload = raw_payload

                # LWT / 在线离线状态处理
                if suffix.lower() == "lwt":
                    text = payload if isinstance(payload, str) else str(payload)
                    is_online = text.lower() not in ("offline", "0", "false")
                    device.is_online = is_online
                    device.save(update_fields=["is_online", "updated_at"])

                    if is_online:
                        lwt_msg = f"设备 [{device.name}] 已上线"
                    else:
                        lwt_msg = f"警告：设备 [{device.name}] 异常离线"
                    SystemLog.objects.create(
                        level=SystemLog.LEVEL_WARN if not is_online else SystemLog.LEVEL_INFO,
                        source="MQTT_LWT",
                        message=lwt_msg,
                        data={"topic": topic, "payload": text, "device_id": device_id},
                        user=device.owner,
                    )
                    return

                # 正常状态上报：执行写入操作
                device.current_state = payload
                device.is_online = True
                device.save(update_fields=["current_state", "is_online", "updated_at"])

                # 记录历史数据
                DeviceData.objects.create(
                    device=device,
                    timestamp=timezone.now(),
                    data=payload,
                )

                # 记录日志：详细说明各字段更新值
                detail_msg = self._format_state_message(device.name, device_id, payload)
                SystemLog.objects.create(
                    level=SystemLog.LEVEL_INFO,
                    source="MQTT_GATEWAY",
                    message=detail_msg,
                    data={"topic": topic, "payload": payload},
                    user=device.owner,
                )

                # 安全告警：温度超过阈值（例如 35°C）
                try:
                    if (
                        # device.type == DeviceType.TEMP_HUMI
                        device.type == DeviceType.TEMPERATURE_HUMIDITY
                        and isinstance(payload, dict)
                        and "temp" in payload
                    ):
                        temp_value = float(payload["temp"])
                        threshold = getattr(settings, "ALERT_TEMP_THRESHOLD", 35.0)
                        if temp_value >= threshold:
                            msg = (
                                f"设备 {device.name}({device_id}) 温度过高：{temp_value}°C，"
                                f"已超过阈值 {threshold}°C"
                            )
                            SystemLog.objects.create(
                                level=SystemLog.LEVEL_WARN,
                                source="ALERT",
                                message=msg,
                                data={"topic": topic, "payload": payload, "threshold": threshold},
                                user=device.owner,
                            )
                            try:
                                mail_admins(subject="[安全告警] 温度过高", message=msg, fail_silently=True)
                            except Exception:
                                pass
                            try:
                                send_email_alerts_for_value(device, "temp", temp_value)
                            except Exception:
                                pass
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"告警逻辑执行失败: {e}"))

                # 通用邮件告警：对上报中的数值字段检查邮件规则
                if isinstance(payload, dict):
                    for field in ("temp", "humi", "light", "pressure"):
                        if field in payload:
                            try:
                                v = float(payload[field])
                                send_email_alerts_for_value(device, field, v)
                            except (ValueError, TypeError):
                                pass
                    # 烟雾告警：二值触发（1=触发，0=未触发）
                    if device.type == DeviceType.SMOKE:
                        triggered = (
                            payload.get("smoke") is True
                            or payload.get("alarm") is True
                            or bool(payload.get("value"))
                        )
                        send_email_alerts_for_value(
                            device, "smoke", 1.0 if triggered else 0.0
                        )

                # 场景规则执行引擎：检查是否有规则被触发
                try:
                    self._check_and_execute_scene_rules(device, payload)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"场景规则执行失败: {e}"))

                self.stdout.write(self.style.SUCCESS(f"成功更新设备 {device_id} 的数据并存入历史表"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"处理逻辑发生异常: {str(e)}"))

        # def on_message(client, userdata, msg):
        #     try:
        #         topic = msg.topic
        #         payload = json.loads(msg.payload.decode())
        #         parts = topic.split("/")
        #         if len(parts) < 2:
        #             return
        #         try:
        #             device_id = int(parts[1])
        #         except ValueError:
        #             return
        #         try:
        #             device = Device.objects.get(pk=device_id)
        #         except Device.DoesNotExist:
        #             return
        #         device.current_state = payload
        #         device.is_online = True
        #         device.save(update_fields=["current_state", "is_online", "updated_at"])
        #         DeviceData.objects.create(
        #             device=device, timestamp=timezone.now(), data=payload
        #         )
        #         SystemLog.objects.create(
        #             level=SystemLog.LEVEL_INFO,
        #             source="MQTT_GATEWAY",
        #             message=f"设备 {device.name}({device_id}) 状态更新",
        #             data={"topic": topic, "payload": payload},
        #         )
        #     except Exception as e:
        #         self.stdout.write(self.style.ERROR(f"处理消息出错: {e}"))

        client = mqtt.Client()
        if config.get("USERNAME"):
            client.username_pw_set(config["USERNAME"], config.get("PASSWORD", ""))
        client.on_connect = on_connect
        client.on_message = on_message
        try:
            client.connect(config["HOST"], config["PORT"], config.get("KEEPALIVE", 60))
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("正在关闭 MQTT 网关…"))
            client.loop_stop()
            client.disconnect()
        except Exception as e:
            self.stdout.write(self.style.ERROR(str(e)))

    def _format_state_message(self, device_name: str, device_id: int, payload: dict) -> str:
        """将状态 payload 格式化为可读的日志消息。"""
        if not isinstance(payload, dict):
            return f"设备 [{device_name}]({device_id}) 状态已更新"
        parts = []
        if "temp" in payload:
            parts.append(f"温度 {payload['temp']}°C")
        if "humi" in payload:
            parts.append(f"湿度 {payload['humi']}%RH")
        if "on" in payload:
            parts.append("开" if payload["on"] else "关")
        if "speed" in payload:
            parts.append(f"档位 {payload['speed']}")
        if "light" in payload:
            parts.append(f"光照 {payload['light']}")
        if "pressure" in payload:
            parts.append(f"气压 {payload['pressure']}")
        for k, v in payload.items():
            if k in ("temp", "humi", "on", "speed", "light", "pressure"):
                continue
            parts.append(f"{k}={v}")
        if not parts:
            return f"设备 [{device_name}]({device_id}) 状态已更新"
        return f"设备 [{device_name}] 上报：{', '.join(parts)}"

    def _format_action_desc(self, action_device_name: str, action_type: str, action_payload: dict) -> str:
        """格式化为场景联动描述。"""
        if action_type == SceneRule.ACTION_SET_TEMP:
            temp = action_payload.get("temp", 26)
            return f"已自动将 {action_device_name} 设置为 {temp}°C"
        if action_type == SceneRule.ACTION_SET_FAN_SPEED:
            speed = action_payload.get("speed", 1)
            return f"已自动将 {action_device_name} 设为 {speed} 档"
        if action_type == SceneRule.ACTION_TURN_ON:
            return f"已自动开启 {action_device_name}"
        if action_type == SceneRule.ACTION_TURN_OFF:
            return f"已自动关闭 {action_device_name}"
        if action_type == SceneRule.ACTION_TOGGLE:
            return f"已自动切换 {action_device_name} 开关"
        return f"已执行 {action_device_name} 动作"

    def _check_and_execute_scene_rules(self, trigger_device: Device, payload: dict):
        """
        检查场景规则是否被触发，如果触发则执行动作。
        """
        from datetime import datetime, time as dt_time
        from mqtt_gateway.utils import publish_device_command

        # 查找所有启用且以该设备为触发设备的规则
        rules = SceneRule.objects.filter(
            enabled=True,
            trigger_device=trigger_device,
        ).select_related("action_device", "trigger_state_device")

        now = timezone.now()
        current_time = now.time()

        for rule in rules:
            # 防抖检查：如果距离上次触发时间太短，跳过
            if rule.last_triggered_at:
                delta = (now - rule.last_triggered_at).total_seconds()
                if delta < rule.debounce_seconds:
                    continue

            # 检查触发条件
            trigger_field_value = payload.get(rule.trigger_field)
            if trigger_field_value is None:
                continue

            try:
                trigger_field_value = float(trigger_field_value)
            except (ValueError, TypeError):
                continue

            triggered = False

            # 1. 阈值上限触发
            if rule.trigger_type == SceneRule.TRIGGER_THRESHOLD_ABOVE:
                threshold = float(rule.trigger_value) if isinstance(rule.trigger_value, (int, float)) else float(rule.trigger_value.get("value", 0))
                triggered = trigger_field_value > threshold

            # 2. 阈值下限触发
            elif rule.trigger_type == SceneRule.TRIGGER_THRESHOLD_BELOW:
                threshold = float(rule.trigger_value) if isinstance(rule.trigger_value, (int, float)) else float(rule.trigger_value.get("value", 0))
                triggered = trigger_field_value < threshold

            # 3. 区间外触发
            elif rule.trigger_type == SceneRule.TRIGGER_RANGE_OUT:
                if isinstance(rule.trigger_value, dict):
                    min_val = float(rule.trigger_value.get("min", 0))
                    max_val = float(rule.trigger_value.get("max", 0))
                    triggered = trigger_field_value < min_val or trigger_field_value > max_val

            # 4. 时间+状态组合触发
            elif rule.trigger_type == SceneRule.TRIGGER_TIME_STATE:
                # 检查时间范围
                time_match = False
                if rule.trigger_time_start and rule.trigger_time_end:
                    if rule.trigger_time_start <= rule.trigger_time_end:
                        # 正常范围（如 09:00-18:00）
                        time_match = rule.trigger_time_start <= current_time <= rule.trigger_time_end
                    else:
                        # 跨天范围（如 23:00-02:00）
                        time_match = current_time >= rule.trigger_time_start or current_time <= rule.trigger_time_end

                # 检查状态设备
                state_match = True
                if rule.trigger_state_device and rule.trigger_state_value:
                    device_state = rule.trigger_state_device.current_state or {}
                    for key, expected_value in rule.trigger_state_value.items():
                        if device_state.get(key) != expected_value:
                            state_match = False
                            break

                triggered = time_match and state_match

            if triggered:
                # 执行动作
                action_payload = {}
                if rule.action_type == SceneRule.ACTION_TOGGLE:
                    current_on = bool(rule.action_device.current_state.get("on", False))
                    action_payload = {"on": not current_on}
                elif rule.action_type == SceneRule.ACTION_SET_TEMP:
                    temp_value = rule.action_value if isinstance(rule.action_value, (int, float)) else rule.action_value.get("temp", 26)
                    action_payload = {"temp": float(temp_value), "on": True}
                elif rule.action_type == SceneRule.ACTION_SET_FAN_SPEED:
                    speed_value = rule.action_value if isinstance(rule.action_value, int) else rule.action_value.get("speed", 1)
                    action_payload = {"speed": int(speed_value), "on": True}
                elif rule.action_type == SceneRule.ACTION_TURN_ON:
                    action_payload = {"on": True}
                elif rule.action_type == SceneRule.ACTION_TURN_OFF:
                    action_payload = {"on": False}

                # 更新动作设备的状态
                state = rule.action_device.current_state.copy()
                state.update(action_payload)
                rule.action_device.current_state = state
                rule.action_device.save(update_fields=["current_state", "updated_at"])

                # 发布 MQTT 命令
                publish_device_command(device_id=rule.action_device.id, payload=action_payload)

                # 更新规则的最后触发时间
                rule.last_triggered_at = now
                rule.save(update_fields=["last_triggered_at"])

                # 记录日志（便于横幅展示）
                action_desc = self._format_action_desc(rule.action_device.name, rule.action_type, action_payload)
                scene_msg = f"场景联动：{action_desc}"
                SystemLog.objects.create(
                    level=SystemLog.LEVEL_INFO,
                    source="SCENE_RULE",
                    message=scene_msg,
                    data={
                        "rule_id": rule.id,
                        "trigger_device_id": trigger_device.id,
                        "action_device_id": rule.action_device.id,
                        "action_payload": action_payload,
                    },
                    user=rule.owner,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"场景规则「{rule.name}」已触发并执行动作"
                    )
                )
