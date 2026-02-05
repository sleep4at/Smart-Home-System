"""
兼容 Channels 的 ASGI 配置文件（如果你用 `django-admin startproject` 可能已存在 smart_home_backend/asgi.py）。
这里提供一个简单版本，后续需要 WebSocket 再补充路由。
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_home_backend.settings")

application = get_asgi_application()

