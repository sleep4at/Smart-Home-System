"""
从项目根目录加载 .env，供各模拟脚本通过 os.getenv 读取配置。
同时提供 MQTT TLS 公共辅助函数。
"""
import os
import ssl
from pathlib import Path

# 项目根目录（Demo_1），用于解析 .env 中的相对证书路径
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv_from_project_root():
    try:
        from dotenv import load_dotenv
        load_dotenv(_PROJECT_ROOT / ".env")
    except ImportError:
        pass


def mqtt_use_tls() -> bool:
    """当前 .env 是否启用了 MQTT TLS。"""
    return os.getenv("MQTT_USE_TLS", "False").lower() in ("true", "1", "yes")


def mqtt_transport_label() -> str:
    """返回当前连接模式描述，用于日志/打印。"""
    return "mqtts (TLS)" if mqtt_use_tls() else "mqtt (no TLS)"


def _resolve_cert_path(path: str | None) -> str | None:
    """将相对路径解析为基于项目根目录的绝对路径；若文件不存在则返回 None。"""
    if not path or not path.strip():
        return None
    path = path.strip()
    p = Path(path)
    if not p.is_absolute():
        p = _PROJECT_ROOT / path
    return str(p) if p.exists() else None


def apply_tls(client) -> None:
    """若 .env 中 MQTT_USE_TLS=True，对 paho MQTT client 做 tls_set。"""
    if not mqtt_use_tls():
        return
    ca_certs = _resolve_cert_path(os.getenv("MQTT_CA_CERTS"))
    certfile = _resolve_cert_path(os.getenv("MQTT_CERTFILE"))
    keyfile = _resolve_cert_path(os.getenv("MQTT_KEYFILE"))
    tls_insecure = os.getenv("MQTT_TLS_INSECURE", "False").lower() in ("true", "1", "yes")
    cert_reqs = ssl.CERT_NONE if tls_insecure else ssl.CERT_REQUIRED

    if cert_reqs == ssl.CERT_REQUIRED and not ca_certs:
        # 未提供或找不到 CA 文件时，使用系统默认 CA（避免 FileNotFoundError）
        ctx = ssl.create_default_context()
        client.tls_set_context(ctx)
    else:
        client.tls_set(
            ca_certs=ca_certs,
            certfile=certfile,
            keyfile=keyfile,
            cert_reqs=cert_reqs,
        )
    if tls_insecure:
        client.tls_insecure_set(True)
