from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminUserRole
from .models import SystemLog
from .serializers import SystemLogSerializer


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
        if user.is_staff or user.is_superuser:
            return qs
        return qs.filter(user__isnull=True) | qs.filter(user=user)
