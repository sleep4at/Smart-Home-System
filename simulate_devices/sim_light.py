#!/usr/bin/env python3
"""
光照传感器 (LIGHT) MQTT 模拟设备。
上报字段：light（光照数值），与网关、前端、邮件告警规则一致。
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
DEVICE_ID = 8
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "home")

LIGHT_MIN = float(os.getenv("SIM_LIGHT_MIN", "2.0"))
LIGHT_MAX = float(os.getenv("SIM_LIGHT_MAX", "2000.0"))
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
        pass  # 光照传感器只读，不处理 cmd

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
            light = round(random.uniform(LIGHT_MIN, LIGHT_MAX), 1)
            payload = {"light": light}
            client.publish(topic_state, json.dumps(payload), qos=1)
            print(f"上报 state: {payload}")
            time.sleep(STATE_INTERVAL_SEC)
    except KeyboardInterrupt:
        client.publish(topic_lwt, "offline", qos=1)
        client.loop_stop()
        client.disconnect()
        print("已退出")


if __name__ == "__main__":
    main()
