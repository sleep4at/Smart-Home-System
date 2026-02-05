"""
MQTT 工具：发布设备控制命令，供后端 API 调用。
"""

import json
import threading
from typing import Optional

import paho.mqtt.client as mqtt
from django.conf import settings

_mqtt_client: Optional[mqtt.Client] = None
_client_lock = threading.Lock()


def get_mqtt_client() -> mqtt.Client:
    """获取全局 MQTT 客户端单例。"""
    global _mqtt_client
    if _mqtt_client is None:
        with _client_lock:
            if _mqtt_client is None:
                config = settings.MQTT_CONFIG
                _mqtt_client = mqtt.Client()
                if config.get("USERNAME"):
                    _mqtt_client.username_pw_set(
                        config["USERNAME"], config.get("PASSWORD", "")
                    )
                try:
                    _mqtt_client.connect(
                        config["HOST"], config["PORT"], config.get("KEEPALIVE", 60)
                    )
                    _mqtt_client.loop_start()
                except Exception as e:
                    print(f"MQTT 连接失败: {e}")
    return _mqtt_client


def publish_device_command(device_id: int, payload: dict) -> None:
    """向主题 home/{device_id}/cmd 发布控制命令。"""
    try:
        config = settings.MQTT_CONFIG
        topic_prefix = config.get("TOPIC_PREFIX", "home")
        topic = f"{topic_prefix}/{device_id}/cmd"
        client = get_mqtt_client()
        message = json.dumps(payload)
        result = client.publish(topic, message, qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"MQTT 发布失败: topic={topic}, rc={result.rc}")
    except Exception as e:
        print(f"发布 MQTT 命令时出错: {e}")
