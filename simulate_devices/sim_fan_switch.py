#!/usr/bin/env python3
"""
风扇开关 (FAN_SWITCH) MQTT 模拟设备。
状态字段：on（bool）, speed（1/2/3）。订阅 cmd，接收 {"on": true/false} 或 {"speed": 1|2|3, "on": true}。
配置从项目根目录 .env 读取（os.getenv）。
"""

import json
import os
import random
import signal
import threading
import time

import paho.mqtt.client as mqtt

try:
    from _env import (
        load_dotenv_from_project_root,
        apply_tls,
        mqtt_transport_label,
        is_interactive_session,
        build_sim_client_id,
    )
    load_dotenv_from_project_root()
except Exception:
    apply_tls = None
    mqtt_transport_label = lambda: "mqtt (明文)"
    is_interactive_session = lambda default=True: default
    build_sim_client_id = lambda kind, did: f"simdev-{kind}-id{did}"

# ========== 配置（环境变量，来自 .env）==========
MQTT_BROKER = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USER") or None
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD") or None
DEVICE_ID = 5
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "home")

INITIAL_ON = os.getenv("SIM_FAN_INITIAL_ON", "false").lower() in ("1", "true", "yes")
INITIAL_SPEED = int(os.getenv("SIM_FAN_INITIAL_SPEED", "1"))
POWER_REPORT_INTERVAL_SEC = float(os.getenv("SIM_POWER_REPORT_INTERVAL_SEC", "10"))
FAN_SPEED_1_W = float(os.getenv("SIM_FAN_SPEED_1_W", "30"))
FAN_SPEED_2_W = float(os.getenv("SIM_FAN_SPEED_2_W", "45"))
FAN_SPEED_3_W = float(os.getenv("SIM_FAN_SPEED_3_W", "60"))
POWER_JITTER_PCT = float(os.getenv("SIM_POWER_JITTER_PCT", "0.05"))
INITIAL_ENERGY_WH = float(os.getenv("SIM_FAN_INITIAL_ENERGY_WH", "0"))
# ================================


def main():
    topic_state = f"{TOPIC_PREFIX}/{DEVICE_ID}/state"
    topic_power = f"{TOPIC_PREFIX}/{DEVICE_ID}/power"
    topic_lwt = f"{TOPIC_PREFIX}/{DEVICE_ID}/lwt"
    topic_cmd = f"{TOPIC_PREFIX}/{DEVICE_ID}/cmd"

    state = {"on": INITIAL_ON, "speed": INITIAL_SPEED}
    energy_wh_total = max(0.0, INITIAL_ENERGY_WH)
    last_power_ts = time.time()
    stop_event = threading.Event()

    def _handle_stop(_signum, _frame):
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _handle_stop)
        except Exception:
            pass

    def calc_power_w():
        if not state.get("on"):
            return 0.0
        speed = int(state.get("speed", 1))
        if speed <= 1:
            base = FAN_SPEED_1_W
        elif speed == 2:
            base = FAN_SPEED_2_W
        else:
            base = FAN_SPEED_3_W
        factor = 1.0 + random.uniform(-POWER_JITTER_PCT, POWER_JITTER_PCT)
        return max(0.0, base * factor)

    def publish_power_snapshot():
        nonlocal energy_wh_total, last_power_ts
        now = time.time()
        dt = max(0.0, now - last_power_ts)
        last_power_ts = now
        power_w = calc_power_w()
        energy_wh_total += power_w * dt / 3600.0
        payload = {
            "power_w": round(power_w, 3),
            "energy_wh_total": round(energy_wh_total, 3),
        }
        client.publish(topic_power, json.dumps(payload), qos=1)

    def power_loop():
        while not stop_event.wait(POWER_REPORT_INTERVAL_SEC):
            publish_power_snapshot()

    def on_connect(client, userdata, flags, rc):
        nonlocal last_power_ts
        if rc != 0:
            print(f"连接失败 rc={rc}")
            return
        print(f"已连接 {MQTT_BROKER}:{MQTT_PORT}")
        client.publish(topic_lwt, "online", qos=1)
        client.publish(topic_state, json.dumps(state), qos=1)
        last_power_ts = time.time()
        publish_power_snapshot()
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
            publish_power_snapshot()
            print("收到 cmd，上报 state:", state)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    client_id = build_sim_client_id("fan", DEVICE_ID)
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
    client.subscribe(topic_cmd, qos=1)
    client.loop_start()
    power_thread = threading.Thread(target=power_loop, daemon=True)
    power_thread.start()

    if is_interactive_session(default=True):
        print("键盘控制: ON 开机 / OFF 关机 / S:1 或 SPEED:2 设档位(1-3)，回车发送（输入 q 退出）")
        try:
            while not stop_event.is_set():
                try:
                    line = input("> ").strip().upper()
                except EOFError:
                    break
                if not line:
                    continue
                if line == "Q" or line == "QUIT":
                    break
                if line == "ON":
                    state["on"] = True
                    client.publish(topic_state, json.dumps(state), qos=1)
                    publish_power_snapshot()
                    print("  -> 已上报: 开机", state)
                elif line == "OFF":
                    state["on"] = False
                    client.publish(topic_state, json.dumps(state), qos=1)
                    publish_power_snapshot()
                    print("  -> 已上报: 关机", state)
                elif line.startswith("S:") or line.startswith("SPEED:"):
                    try:
                        part = line.split(":", 1)[1].strip()
                        s = int(part)
                        if s in (1, 2, 3):
                            state["speed"] = s
                            state["on"] = True
                            client.publish(topic_state, json.dumps(state), qos=1)
                            publish_power_snapshot()
                            print("  -> 已上报: 档位", state)
                        else:
                            print("  档位须为 1、2 或 3")
                    except (ValueError, IndexError):
                        print("  无效档位，请输入 S:1 / S:2 / S:3")
                else:
                    print("  未知命令，请输入 ON / OFF / S:2")
        except KeyboardInterrupt:
            pass
    else:
        print("非交互模式运行（SIM_INTERACTIVE=false 或无终端），等待后端 cmd 指令...")
        try:
            while not stop_event.wait(1.0):
                pass
        except KeyboardInterrupt:
            pass
    stop_event.set()
    power_thread.join(timeout=1)
    publish_power_snapshot()
    client.publish(topic_lwt, "offline", qos=1)
    client.loop_stop()
    client.disconnect()
    print("已退出")


if __name__ == "__main__":
    main()
