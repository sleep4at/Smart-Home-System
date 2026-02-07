from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminUserRole
from .models import EmailAlertRule, SystemLog
from .serializers import EmailAlertRuleSerializer, SystemLogSerializer


class SystemLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    系统日志列表：
    - 管理员：查看所有日志
    - 普通用户：仅查看与自己相关或无 user 关联的日志
    """

    serializer_class = SystemLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = SystemLog.objects.all()

        level = self.request.query_params.get("level")
        if level:
            qs = qs.filter(level=level)
        source = self.request.query_params.get("source")
        if source:
            qs = qs.filter(source=source)

        if user.is_staff or user.is_superuser:
            pass
        else:
            qs = qs.filter(user__isnull=True) | qs.filter(user=user)

        limit = self.request.query_params.get("limit")
        if limit is not None:
            try:
                n = min(int(limit), 500)
                qs = qs[:n]
            except ValueError:
                pass
        return qs


class EmailAlertRuleViewSet(viewsets.ModelViewSet):
    """邮件告警规则 CRUD，仅管理员。"""

    queryset = EmailAlertRule.objects.all().select_related("trigger_device")
    serializer_class = EmailAlertRuleSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    @action(detail=True, methods=["post"])
    def toggle_enabled(self, request, pk=None):
        rule = self.get_object()
        rule.enabled = not rule.enabled
        rule.save(update_fields=["enabled"])
        return Response({"enabled": rule.enabled})
