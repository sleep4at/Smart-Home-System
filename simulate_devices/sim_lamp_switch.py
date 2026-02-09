#!/usr/bin/env python3
"""
灯具开关 (LAMP_SWITCH) MQTT 模拟设备。
状态字段：on（bool）。订阅 cmd，接收后端下发的 {"on": true/false} 并回写 state。
配置从项目根目录 .env 读取（os.getenv），隐私参数勿写死在代码中。
"""

import json
import os
import time

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
DEVICE_ID = 2
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "home")

INITIAL_ON = os.getenv("SIM_LAMP_INITIAL_ON", "false").lower() in ("1", "true", "yes")
# ================================


def main():
    topic_state = f"{TOPIC_PREFIX}/{DEVICE_ID}/state"
    topic_lwt = f"{TOPIC_PREFIX}/{DEVICE_ID}/lwt"
    topic_cmd = f"{TOPIC_PREFIX}/{DEVICE_ID}/cmd"

    state = {"on": INITIAL_ON}

    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            print(f"连接失败 rc={rc}")
            return
        print(f"已连接 {MQTT_BROKER}:{MQTT_PORT}")
        client.publish(topic_lwt, "online", qos=1)
        client.publish(topic_state, json.dumps(state), qos=1)
        print("已发布 LWT: online, 初始 state:", state)

    def on_message(client, userdata, msg):
        nonlocal state
        try:
            payload = json.loads(msg.payload.decode())
            if "on" in payload:
                state["on"] = bool(payload["on"])
                client.publish(topic_state, json.dumps(state), qos=1)
                print("收到 cmd，上报 state:", state)
        except (json.JSONDecodeError, TypeError):
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
    client.subscribe(topic_cmd, qos=1)
    client.loop_start()

    print("键盘控制: 输入 ON 开灯 / OFF 关灯，回车发送（输入 q 退出）")
    try:
        while True:
            line = input("> ").strip().upper()
            if not line:
                continue
            if line == "Q" or line == "QUIT":
                break
            if line == "ON":
                state["on"] = True
                client.publish(topic_state, json.dumps(state), qos=1)
                print("  -> 已上报: 开灯", state)
            elif line == "OFF":
                state["on"] = False
                client.publish(topic_state, json.dumps(state), qos=1)
                print("  -> 已上报: 关灯", state)
            else:
                print("  未知命令，请输入 ON / OFF")
    except (KeyboardInterrupt, EOFError):
        pass
    client.publish(topic_lwt, "offline", qos=1)
    client.loop_stop()
    client.disconnect()
    print("已退出")


if __name__ == "__main__":
    main()
