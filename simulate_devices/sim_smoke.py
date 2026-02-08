#!/usr/bin/env python3
"""
烟雾传感器 (SMOKE) MQTT 模拟设备。
上报字段：smoke（bool）或 alarm（bool）或 value（0/1），与网关邮件告警、前端「正常/警告」一致。
配置从项目根目录 .env 读取（os.getenv）。
"""

import json
import os
import random
import time

import paho.mqtt.client as mqtt

try:
    from _env import load_dotenv_from_project_root
    load_dotenv_from_project_root()
except Exception:
    pass

# ========== 配置（环境变量，来自 .env）==========
MQTT_BROKER = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USER") or None
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD") or None
DEVICE_ID = 7
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "home")

PROB_ALARM = float(os.getenv("SIM_SMOKE_PROB_ALARM", "0.15"))
STATE_INTERVAL_SEC = float(os.getenv("SIM_STATE_INTERVAL_SEC", "60.0"))
# ================================


def main():
    topic_state = f"{TOPIC_PREFIX}/{DEVICE_ID}/state"
    topic_lwt = f"{TOPIC_PREFIX}/{DEVICE_ID}/lwt"
    topic_cmd = f"{TOPIC_PREFIX}/{DEVICE_ID}/cmd"

    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            print(f"连接失败 rc={rc}")
            return
        print(f"已连接 {MQTT_BROKER}:{MQTT_PORT}")
        client.publish(topic_lwt, "online", qos=1)
        print("已发布 LWT: online")

    def on_message(client, userdata, msg):
        pass  # 烟雾传感器只读，不处理 cmd

    client = mqtt.Client()
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD or "")
    client.will_set(topic_lwt, "offline", qos=1, retain=False)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    client.subscribe(topic_cmd, qos=1)

    try:
        while True:
            triggered = random.random() < PROB_ALARM
            # 与网关、前端一致：smoke / alarm / value
            payload = {
                "smoke": triggered,
                "alarm": triggered,
                "value": 1 if triggered else 0,
            }
            client.publish(topic_state, json.dumps(payload), qos=1)
            print(f"上报 state: {'警告' if triggered else '正常'} {payload}")
            time.sleep(STATE_INTERVAL_SEC)
    except KeyboardInterrupt:
        client.publish(topic_lwt, "offline", qos=1)
        client.loop_stop()
        client.disconnect()
        print("已退出")


if __name__ == "__main__":
    main()
