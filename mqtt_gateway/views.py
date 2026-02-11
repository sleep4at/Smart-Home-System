"""MQTT 相关 API。"""

import json
import secrets
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.cache import cache
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

STREAM_TOKEN_SALT = "mqtt_gateway.realtime_stream"
STREAM_TOKEN_CACHE_PREFIX = "mqtt_gateway:stream_token:used:"
STREAM_TOKEN_TTL_SECONDS = max(int(getattr(settings, "REALTIME_STREAM_TOKEN_TTL_SECONDS", 30)), 5)


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def realtime_stream_token(request):
    """
    GET /api/realtime/stream-token/
    返回短时、一次性使用的 SSE 票据，避免把主 access token 暴露在 URL 查询参数。
    """
    payload = {
        "uid": int(request.user.id),
        "nonce": secrets.token_urlsafe(12),
    }
    token = signing.dumps(payload, salt=STREAM_TOKEN_SALT, compress=True)
    return Response(
        {
            "stream_token": token,
            "expires_in": STREAM_TOKEN_TTL_SECONDS,
        }
    )


def _consume_stream_token(token):
    try:
        payload = signing.loads(
            token,
            salt=STREAM_TOKEN_SALT,
            max_age=STREAM_TOKEN_TTL_SECONDS,
        )
    except signing.BadSignature:
        return None

    uid = payload.get("uid")
    nonce = payload.get("nonce")
    if uid is None or not nonce:
        return None

    # 一次性票据：同一 nonce 仅允许消费一次，减少日志泄露后的重放窗口。
    if not cache.add(f"{STREAM_TOKEN_CACHE_PREFIX}{nonce}", "1", timeout=STREAM_TOKEN_TTL_SECONDS):
        return None

    user_model = get_user_model()
    try:
        return user_model.objects.get(pk=uid, is_active=True)
    except user_model.DoesNotExist:
        return None


def _authenticate_stream_user(request):
    """
    EventSource 原生不支持自定义 Authorization header，
    优先使用短时一次性 stream_token 鉴权，避免长期 access token 出现在 URL。
    """
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return user

    stream_token = (request.GET.get("stream_token") or request.GET.get("st") or "").strip()
    if stream_token:
        user = _consume_stream_token(stream_token)
        if user is not None:
            request.user = user
            return user

    # 兼容旧前端（默认关闭）
    allow_legacy_query_access_token = bool(
        getattr(settings, "REALTIME_STREAM_ALLOW_LEGACY_ACCESS_TOKEN_QUERY", False)
    )
    if not allow_legacy_query_access_token:
        return None

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
