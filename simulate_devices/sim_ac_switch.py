#!/usr/bin/env python3
"""
空调开关 (AC_SWITCH) MQTT 模拟设备。
状态字段：on（bool）, temp（温度 °C）。订阅 cmd，接收 {"on": true/false} 或 {"temp": 16-30, "on": true}。
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
DEVICE_ID = 6
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "home")

INITIAL_ON = os.getenv("SIM_AC_INITIAL_ON", "false").lower() in ("1", "true", "yes")
INITIAL_TEMP = int(os.getenv("SIM_AC_INITIAL_TEMP", "26"))
TEMP_MIN = int(os.getenv("SIM_AC_TEMP_MIN", "16"))
TEMP_MAX = int(os.getenv("SIM_AC_TEMP_MAX", "30"))
# ================================


def main():
    topic_state = f"{TOPIC_PREFIX}/{DEVICE_ID}/state"
    topic_lwt = f"{TOPIC_PREFIX}/{DEVICE_ID}/lwt"
    topic_cmd = f"{TOPIC_PREFIX}/{DEVICE_ID}/cmd"

    state = {"on": INITIAL_ON, "temp": INITIAL_TEMP}

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
            if "temp" in payload:
                t = int(payload["temp"])
                state["temp"] = max(TEMP_MIN, min(TEMP_MAX, t))
                state["on"] = True  # 设置温度时后端会带 on: True
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

    print("键盘控制: ON 开机 / OFF 关机 / T:26 或 TEMP:26 设温度(16-30)，回车发送（输入 q 退出）")
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
            elif line.startswith("T:") or line.startswith("TEMP:"):
                try:
                    part = line.split(":", 1)[1].strip()
                    t = int(part)
                    state["temp"] = max(TEMP_MIN, min(TEMP_MAX, t))
                    state["on"] = True
                    client.publish(topic_state, json.dumps(state), qos=1)
                    print("  -> 已上报: 设温", state)
                except (ValueError, IndexError):
                    print(f"  无效温度，请输入 T:{TEMP_MIN}-{TEMP_MAX}")
            else:
                print("  未知命令，请输入 ON / OFF / T:26")
    except (KeyboardInterrupt, EOFError):
        pass
    client.publish(topic_lwt, "offline", qos=1)
    client.loop_stop()
    client.disconnect()
    print("已退出")


if __name__ == "__main__":
    main()
