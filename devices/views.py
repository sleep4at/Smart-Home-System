from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminUserRole
from .constants import DeviceType
from .models import Device, DeviceData
from .permissions import IsDeviceOwnerOrAdmin
from .serializers import (
    DeviceHistoryPointSerializer,
    DeviceHistoryQuerySerializer,
    DeviceSerializer,
)


class DeviceViewSet(viewsets.ModelViewSet):
    """
    设备管理与基本控制。
    - 管理员：增删改查所有设备
    - 普通用户：只读/控制自己名下设备
    """

    queryset = Device.objects.all().order_by("id")
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_staff or user.is_superuser:
            # 管理员可以看到所有设备（包括公共和私人）
            return qs
        # 普通用户：自己名下的设备 + 公共设备
        return qs.filter(owner=user) | qs.filter(is_public=True)

    def get_permissions(self):
        # 写操作（POST/PUT/PATCH/DELETE）只允许管理员
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminUserRole()]
        if self.action in ("retrieve", "list", "toggle"):
            return [IsAuthenticated(), IsDeviceOwnerOrAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        # 管理员创建设备时可选指定 owner
        serializer.save()

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """
        开关类设备的开/关命令。
        这里只更新数据库 current_state，并预留发布 MQTT 命令的钩子。
        """
        device: Device = self.get_object()
        payload = request.data or {}
        desired_state = payload.get("state")

        if desired_state is None:
            # 简单 toggle：如果 current_state 有 on 字段则取反
            current = bool(device.current_state.get("on"))
            desired_state = {"on": not current}
        elif isinstance(desired_state, bool):
            desired_state = {"on": desired_state}

        # 更新 current_state
        state = device.current_state.copy()
        state.update(desired_state)
        device.current_state = state
        device.save(update_fields=["current_state", "updated_at"])

        from mqtt_gateway.utils import publish_device_command
        publish_device_command(device_id=device.id, payload=desired_state)

        return Response({"current_state": device.current_state})

    @action(detail=True, methods=["post"])
    def set_temp(self, request, pk=None):
        """
        设置空调温度。
        """
        device: Device = self.get_object()
        if device.type != DeviceType.AC_SWITCH:
            return Response(
                {"error": "该设备不是空调设备"}, status=status.HTTP_400_BAD_REQUEST
            )

        temp = request.data.get("temp")
        if temp is None:
            return Response(
                {"error": "缺少 temp 参数"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            temp = float(temp)
        except (ValueError, TypeError):
            return Response(
                {"error": "温度值必须是数字"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 更新 current_state
        state = device.current_state.copy()
        state["temp"] = temp
        state["on"] = True  # 设置温度时自动开启
        device.current_state = state
        device.save(update_fields=["current_state", "updated_at"])

        from mqtt_gateway.utils import publish_device_command
        publish_device_command(device_id=device.id, payload={"temp": temp, "on": True})

        return Response({"current_state": device.current_state})

    @action(detail=True, methods=["post"])
    def set_fan_speed(self, request, pk=None):
        """
        设置风扇档位（1/2/3）。
        """
        device: Device = self.get_object()
        if device.type != DeviceType.FAN_SWITCH:
            return Response(
                {"error": "该设备不是风扇设备"}, status=status.HTTP_400_BAD_REQUEST
            )

        speed = request.data.get("speed")
        if speed is None:
            return Response(
                {"error": "缺少 speed 参数"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            speed = int(speed)
            if speed not in [1, 2, 3]:
                raise ValueError("档位必须是 1、2 或 3")
        except (ValueError, TypeError):
            return Response(
                {"error": "档位必须是 1、2 或 3"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 更新 current_state
        state = device.current_state.copy()
        state["speed"] = speed
        state["on"] = True  # 设置档位时自动开启
        device.current_state = state
        device.save(update_fields=["current_state", "updated_at"])

        from mqtt_gateway.utils import publish_device_command
        publish_device_command(device_id=device.id, payload={"speed": speed, "on": True})

        return Response({"current_state": device.current_state})


class DeviceHistoryView(APIView):
    """
    /api/devices/{id}/history/?range=24h|3d|7d
    返回设备历史数据，用于前端画图。
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        try:
            device = Device.objects.get(pk=pk)
        except Device.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        perm = IsDeviceOwnerOrAdmin()
        if not perm.has_object_permission(request, self, device):
            return Response(status=status.HTTP_403_FORBIDDEN)

        query_serializer = DeviceHistoryQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        start, end = query_serializer.get_time_range()

        qs = (
            DeviceData.objects.filter(device=device, timestamp__gte=start, timestamp__lte=end)
            .order_by("timestamp")
        )
        data = DeviceHistoryPointSerializer(qs, many=True).data
        return Response({"device_id": device.id, "range": query_serializer.validated_data.get("range", "24h"), "points": data})
        

class DeviceTypeListView(APIView):
    """
    提供设备类型选项，供前端“添加/编辑设备”下拉使用。
    """

    permission_classes = [IsAuthenticated & IsAdminUserRole]

    def get(self, request):
        data = [
            {"value": choice.value, "label": choice.label}
            for choice in DeviceType
        ]
        return Response(data)
