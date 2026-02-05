"""MQTT 相关 API。"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminUserRole
from mqtt_gateway.utils import get_mqtt_client


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUserRole])
def mqtt_status(request):
    """GET /api/mqtt/status/ 返回 MQTT 连接状态（仅管理员）。"""
    try:
        client = get_mqtt_client()
        return Response({"connected": client.is_connected()})
    except Exception as e:
        return Response(
            {"connected": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
