"""
运行 MQTT 网关：订阅 home/+/state，更新设备状态与历史数据。
用法：python3 manage.py run_mqtt_gateway
"""

import json

import paho.mqtt.client as mqtt
from django.conf import settings
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.utils import timezone

from devices.constants import DeviceType
from devices.models import Device, DeviceData
from logs_app.models import SystemLog


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
                    # 约定：payload 为 "offline"/"online"
                    text = payload if isinstance(payload, str) else str(payload)
                    is_online = text.lower() not in ("offline", "0", "false")
                    device.is_online = is_online
                    device.save(update_fields=["is_online", "updated_at"])

                    SystemLog.objects.create(
                        level=SystemLog.LEVEL_WARN if not is_online else SystemLog.LEVEL_INFO,
                        source="MQTT_LWT",
                        message=f"设备 {device.name}({device_id}) LWT 报文：{text}",
                        data={"topic": topic, "payload": text},
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
                    data=payload
                )

                # 记录日志
                SystemLog.objects.create(
                    level=SystemLog.LEVEL_INFO,
                    source="MQTT_GATEWAY",
                    message=f"设备 {device.name}({device_id}) 状态已更新",
                    data={"topic": topic, "payload": payload},
                    user=device.owner,
                )

                # 安全告警：温度超过阈值（例如 35°C）
                try:
                    if (
                        device.type == DeviceType.TEMP_HUMI
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
                            # 邮件通知管理员（依赖 Django ADMINS / 邮件配置）
                            try:
                                mail_admins(subject="[安全告警] 温度过高", message=msg, fail_silently=True)
                            except Exception:
                                # 邮件失败不应影响主流程
                                pass
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"告警逻辑执行失败: {e}"))

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
