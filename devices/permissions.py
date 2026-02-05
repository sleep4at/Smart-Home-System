from rest_framework.permissions import BasePermission


class IsDeviceOwnerOrAdmin(BasePermission):
    """
    普通用户只能访问/控制自己名下的设备；管理员可访问所有设备。
    """

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        return obj.owner_id == user.id

