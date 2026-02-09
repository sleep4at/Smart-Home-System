#!/usr/bin/env python3
"""
风扇开关 (FAN_SWITCH) MQTT 模拟设备。
状态字段：on（bool）, speed（1/2/3）。订阅 cmd，接收 {"on": true/false} 或 {"speed": 1|2|3, "on": true}。
配置从项目根目录 .env 读取（os.getenv）。
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
DEVICE_ID = 5
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "home")

INITIAL_ON = os.getenv("SIM_FAN_INITIAL_ON", "false").lower() in ("1", "true", "yes")
INITIAL_SPEED = int(os.getenv("SIM_FAN_INITIAL_SPEED", "1"))
# ================================


def main():
    topic_state = f"{TOPIC_PREFIX}/{DEVICE_ID}/state"
    topic_lwt = f"{TOPIC_PREFIX}/{DEVICE_ID}/lwt"
    topic_cmd = f"{TOPIC_PREFIX}/{DEVICE_ID}/cmd"

    state = {"on": INITIAL_ON, "speed": INITIAL_SPEED}

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
            if "speed" in payload:
                s = int(payload["speed"])
                if s in (1, 2, 3):
                    state["speed"] = s
                    state["on"] = True
            client.publish(topic_state, json.dumps(state), qos=1)
            print("收到 cmd，上报 state:", state)
        except (json.JSONDecodeError, TypeError, ValueError):
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

    print("键盘控制: ON 开机 / OFF 关机 / S:1 或 SPEED:2 设档位(1-3)，回车发送（输入 q 退出）")
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
                print("  -> 已上报: 开机", state)
            elif line == "OFF":
                state["on"] = False
                client.publish(topic_state, json.dumps(state), qos=1)
                print("  -> 已上报: 关机", state)
            elif line.startswith("S:") or line.startswith("SPEED:"):
                try:
                    part = line.split(":", 1)[1].strip()
                    s = int(part)
                    if s in (1, 2, 3):
                        state["speed"] = s
                        state["on"] = True
                        client.publish(topic_state, json.dumps(state), qos=1)
                        print("  -> 已上报: 档位", state)
                    else:
                        print("  档位须为 1、2 或 3")
                except (ValueError, IndexError):
                    print("  无效档位，请输入 S:1 / S:2 / S:3")
            else:
                print("  未知命令，请输入 ON / OFF / S:2")
    except (KeyboardInterrupt, EOFError):
        pass
    client.publish(topic_lwt, "offline", qos=1)
    client.loop_stop()
    client.disconnect()
    print("已退出")


if __name__ == "__main__":
    main()
