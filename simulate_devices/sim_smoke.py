#!/usr/bin/env python3
"""
烟雾传感器 (SMOKE) MQTT 模拟设备。
仅通过键盘输入上报状态：输入「触发」类命令上报告警，输入「取消」类命令上报正常。
上报字段：smoke / alarm / value，与网关、前端「正常/警告」一致。
"""

import json
import os

import paho.mqtt.client as mqtt

try:
    from _env import load_dotenv_from_project_root, apply_tls, mqtt_transport_label
    load_dotenv_from_project_root()
except Exception:
    apply_tls = None
    mqtt_transport_label = lambda: "mqtt (明文)"

# ========== 配置（环境变量，来自 .env）==========
MQTT_BROKER = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USER") or None
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD") or None
DEVICE_ID = 7
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "home")
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
        client.publish(topic_state, json.dumps({"smoke": False, "alarm": False, "value": 0}), qos=1)
        print("已发布 LWT: online，初始状态: 正常")

    def on_message(client, userdata, msg):
        pass

    client = mqtt.Client()
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD or "")
    if apply_tls:
        apply_tls(client)
    print(f"连接模式: {mqtt_transport_label()}")
    client.will_set(topic_lwt, "offline", qos=1, retain=False)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    client.subscribe(topic_cmd, qos=1)

    trigger_keywords = {"1", "触发", "报警", "告警", "on", "alarm", "y", "yes"}
    normal_keywords = {"0", "正常", "取消", "关闭", "off", "normal", "n", "no"}

    print("键盘控制：输入「1/触发/报警」上报告警 → 磁贴显示警告；输入「0/正常/取消」上报正常；输入 q 退出")

    try:
        while True:
            line = input("> ").strip()
            if not line:
                continue
            t, t_lower = line, line.lower()
            if t_lower in ("q", "quit"):
                break
            if t_lower in trigger_keywords or t in trigger_keywords:
                payload = {"smoke": True, "alarm": True, "value": 1}
                client.publish(topic_state, json.dumps(payload), qos=1)
                print("  -> 已上报: 警告（告警）", payload)
            elif t_lower in normal_keywords or t in normal_keywords:
                payload = {"smoke": False, "alarm": False, "value": 0}
                client.publish(topic_state, json.dumps(payload), qos=1)
                print("  -> 已上报: 正常", payload)
            else:
                print("  未知命令。请输入 1/触发/报警 或 0/正常/取消")
    except (KeyboardInterrupt, EOFError):
        pass
    client.publish(topic_lwt, "offline", qos=1)
    client.loop_stop()
    client.disconnect()
    print("已退出")


if __name__ == "__main__":
    main()
