from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminUserRole
from devices.permissions import IsDeviceOwnerOrAdmin
from .models import SceneRule
from .serializers import SceneRuleSerializer


class SceneRuleViewSet(viewsets.ModelViewSet):
    """
    场景规则管理。
    - 普通用户：只能管理自己的规则
    - 管理员：可以管理所有规则
    """

    serializer_class = SceneRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = SceneRule.objects.all().select_related(
            "owner", "trigger_device", "action_device", "trigger_state_device"
        )
        if user.is_staff or user.is_superuser:
            return qs
        return qs.filter(owner=user)

    def perform_create(self, serializer):
        # 创建时自动设置 owner 为当前用户
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        # 写操作需要权限校验：普通用户只能操作自己的规则
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated()]
        return super().get_permissions()

    def check_object_permissions(self, request, obj):
        """检查对象权限：普通用户只能操作自己的规则，管理员可以操作所有。"""
        super().check_object_permissions(request, obj)
        if not (request.user.is_staff or request.user.is_superuser):
            if obj.owner_id != request.user.id:
                self.permission_denied(request, message="您只能管理自己的场景规则")

    @action(detail=True, methods=["post"])
    def toggle_enabled(self, request, pk=None):
        """切换规则的启用/禁用状态。"""
        rule = self.get_object()
        rule.enabled = not rule.enabled
        rule.save(update_fields=["enabled"])
        return Response({"enabled": rule.enabled})
