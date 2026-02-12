#!/usr/bin/env python3
"""
人体感应 (PIR) MQTT 模拟设备。
上报字段：motion（bool）或 value（0/1），与前端磁贴「未探测/已探测」一致。
配置从项目根目录 .env 读取（os.getenv）。
"""

import json
import os
import random
import time

import paho.mqtt.client as mqtt

try:
    from _env import (
        load_dotenv_from_project_root,
        apply_tls,
        mqtt_transport_label,
        build_sim_client_id,
    )
    load_dotenv_from_project_root()
except Exception:
    apply_tls = None
    mqtt_transport_label = lambda: "mqtt (明文)"
    build_sim_client_id = lambda kind, did: f"simdev-{kind}-id{did}"

# ========== 配置（环境变量，来自 .env）==========
MQTT_BROKER = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USER") or None
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD") or None
DEVICE_ID = 4
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "home")

PROB_DETECTED = float(os.getenv("SIM_PIR_PROB_DETECTED", "0.3"))
STATE_INTERVAL_SEC = float(os.getenv("SIM_STATE_INTERVAL_SEC", "10.0"))
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
        pass  # PIR 只读，不处理 cmd

    client_id = build_sim_client_id("pir", DEVICE_ID)
    client = mqtt.Client(client_id=client_id)
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD or "")
    if apply_tls:
        apply_tls(client)
    print(f"连接模式: {mqtt_transport_label()} | client_id={client_id}")
    client.will_set(topic_lwt, "offline", qos=1, retain=False)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    client.subscribe(topic_cmd, qos=1)

    try:
        while True:
            detected = random.random() < PROB_DETECTED
            # 与前端 DeviceTile 一致：motion / pir / value
            payload = {"motion": detected, "value": 1 if detected else 0}
            client.publish(topic_state, json.dumps(payload), qos=1)
            print(f"上报 state: {'已探测' if detected else '未探测'} {payload}")
            time.sleep(STATE_INTERVAL_SEC)
    except KeyboardInterrupt:
        client.publish(topic_lwt, "offline", qos=1)
        client.loop_stop()
        client.disconnect()
        print("已退出")


if __name__ == "__main__":
    main()
