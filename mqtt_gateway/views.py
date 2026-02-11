"""MQTT 相关 API。"""

import json
import time

from django.db import close_old_connections
from django.db.models import Count, Max
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from devices.models import Device
from devices.serializers import DeviceSerializer
from logs_app.models import SystemLog
from mqtt_gateway.utils import get_mqtt_client


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mqtt_status(request):
    """GET /api/mqtt/status/ 返回 MQTT 连接状态（已登录用户均可调用，用于横幅提示）。"""
    try:
        client = get_mqtt_client()
        return Response({"connected": client.is_connected()})
    except Exception as e:
        return Response(
            {"connected": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _authenticate_stream_user(request):
    """
    EventSource 原生不支持自定义 Authorization header，
    这里兼容 ?access_token=xxx 的方式进行 JWT 鉴权。
    """
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return user

    token = (request.GET.get("access_token") or request.GET.get("token") or "").strip()
    if not token:
        return None

    request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    auth = JWTAuthentication()
    try:
        result = auth.authenticate(request)
    except (InvalidToken, TokenError):
        return None
    if not result:
        return None
    user, _ = result
    request.user = user
    return user


def _visible_devices_qs(user):
    qs = Device.objects.all().order_by("id")
    if user.is_staff or user.is_superuser:
        return qs
    return (qs.filter(owner=user) | qs.filter(is_public=True)).distinct().order_by("id")


def _visible_logs_qs(user):
    qs = SystemLog.objects.all()
    if user.is_staff or user.is_superuser:
        return qs
    return (qs.filter(user__isnull=True) | qs.filter(user=user)).distinct()


def _mqtt_connected() -> bool:
    try:
        return bool(get_mqtt_client().is_connected())
    except Exception:
        return False


def _sse(event: str, data) -> str:
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


def realtime_stream(request):
    """
    GET /api/realtime/stream/
    通过 SSE 推送日志、MQTT状态、设备列表变更，替代前端高频轮询。
    """
    user = _authenticate_stream_user(request)
    if user is None:
        return HttpResponse("Unauthorized", status=401)

    def event_stream():
        close_old_connections()
        logs_qs = _visible_logs_qs(user)
        latest_log = logs_qs.order_by("-id").values_list("id", flat=True).first() or 0
        last_log_id = int(latest_log)
        last_mqtt = _mqtt_connected()
        device_signature = None

        init_devices_qs = _visible_devices_qs(user)
        init_devices = DeviceSerializer(init_devices_qs, many=True).data
        yield _sse(
            "init",
            {
                "last_log_id": last_log_id,
                "mqtt_connected": last_mqtt,
                "devices": init_devices,
            },
        )

        try:
            while True:
                close_old_connections()

                # 新日志增量推送
                for log in _visible_logs_qs(user).filter(id__gt=last_log_id).order_by("id")[:200]:
                    last_log_id = max(last_log_id, int(log.id))
                    yield _sse(
                        "log",
                        {
                            "id": log.id,
                            "source": log.source,
                            "level": log.level,
                            "message": log.message,
                            "created_at": log.created_at.isoformat(),
                        },
                    )

                # MQTT 在线状态变化推送
                mqtt_now = _mqtt_connected()
                if mqtt_now != last_mqtt:
                    last_mqtt = mqtt_now
                    yield _sse("mqtt_status", {"connected": mqtt_now})

                # 设备列表变化推送（基于 count + max(updated_at) 轻量判定）
                devices_qs = _visible_devices_qs(user)
                agg = devices_qs.aggregate(
                    count=Count("id"),
                    max_updated=Max("updated_at"),
                )
                max_updated = agg.get("max_updated")
                signature = f"{agg.get('count', 0)}|{max_updated.isoformat() if max_updated else ''}"
                if signature != device_signature:
                    device_signature = signature
                    yield _sse("devices", {"items": DeviceSerializer(devices_qs, many=True).data})

                # SSE 保活注释行，避免中间层超时断开
                yield ": ping\n\n"
                time.sleep(1.5)
        except (GeneratorExit, BrokenPipeError, ConnectionResetError):
            return

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream; charset=utf-8")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
