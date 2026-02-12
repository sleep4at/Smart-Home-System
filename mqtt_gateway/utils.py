"""
MQTT 工具：发布设备控制命令，供后端 API 调用。
"""

import json
import secrets
import ssl
import threading
from pathlib import Path
from typing import Optional

import paho.mqtt.client as mqtt
from django.conf import settings

_mqtt_client: Optional[mqtt.Client] = None
_client_lock = threading.Lock()

# 项目根目录，用于解析 .env 中的相对证书路径
_BASE_DIR = Path(settings.BASE_DIR) if hasattr(settings, "BASE_DIR") else Path(__file__).resolve().parent.parent


def _sanitize_client_id(value: str, fallback: str = "smarthome") -> str:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    cleaned = "".join(ch if ch in allowed else "-" for ch in (value or "").strip())
    cleaned = cleaned.strip("-")
    if not cleaned:
        cleaned = fallback
    # 常见 Broker 均支持 >23，这里保守截断到 64。
    return cleaned[:64]


def build_mqtt_client_id(config: dict, role: str) -> str:
    """
    构造 MQTT ClientID：
    - 优先使用显式配置（MQTT_CLIENT_ID_GATEWAY / MQTT_CLIENT_ID_API）
    - 否则使用 {prefix}-{role}-{random_suffix}
    """
    role_key = f"CLIENT_ID_{role.upper()}"
    explicit = config.get(role_key)
    if isinstance(explicit, str) and explicit.strip():
        return _sanitize_client_id(explicit)

    prefix = _sanitize_client_id(str(config.get("CLIENT_ID_PREFIX", "smarthome")), fallback="smarthome")
    try:
        suffix_len = int(config.get("CLIENT_ID_SUFFIX_LEN", 6))
    except (TypeError, ValueError):
        suffix_len = 6
    suffix_len = max(4, min(16, suffix_len))
    suffix = secrets.token_hex((suffix_len + 1) // 2)[:suffix_len]
    return _sanitize_client_id(f"{prefix}-{role}-{suffix}")


def _resolve_cert_path(path: Optional[str]) -> Optional[str]:
    """将相对路径解析为基于项目根目录的绝对路径；若文件不存在则返回 None。"""
    if not path or not path.strip():
        return None
    path = path.strip()
    p = Path(path)
    if not p.is_absolute():
        p = _BASE_DIR / path
    return str(p) if p.exists() else None


def _apply_tls(client: mqtt.Client, config: dict) -> None:
    """若配置中启用了 TLS，对 client 做 tls_set。"""
    if not config.get("USE_TLS"):
        return
    ca_certs = _resolve_cert_path(config.get("CA_CERTS"))
    certfile = _resolve_cert_path(config.get("CERTFILE"))
    keyfile = _resolve_cert_path(config.get("KEYFILE"))
    cert_reqs = ssl.CERT_REQUIRED if not config.get("TLS_INSECURE") else ssl.CERT_NONE

    if cert_reqs == ssl.CERT_REQUIRED and not ca_certs:
        # 未提供或找不到 CA 文件时，使用系统默认 CA（避免 FileNotFoundError）
        ctx = ssl.create_default_context()
        client.tls_set_context(ctx)
    else:
        client.tls_set(
            ca_certs=ca_certs or None,
            certfile=certfile or None,
            keyfile=keyfile or None,
            cert_reqs=cert_reqs,
        )
    if config.get("TLS_INSECURE"):
        client.tls_insecure_set(True)


def get_mqtt_client() -> mqtt.Client:
    """获取全局 MQTT 客户端单例。"""
    global _mqtt_client
    if _mqtt_client is None:
        with _client_lock:
            if _mqtt_client is None:
                config = settings.MQTT_CONFIG
                client_id = build_mqtt_client_id(config, role="api")
                _mqtt_client = mqtt.Client(client_id=client_id)
                if config.get("USERNAME"):
                    _mqtt_client.username_pw_set(
                        config["USERNAME"], config.get("PASSWORD", "")
                    )
                _apply_tls(_mqtt_client, config)
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
