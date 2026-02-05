from rest_framework.permissions import BasePermission


class IsAdminUserRole(BasePermission):
    """
    简单的管理员判断：使用 is_staff / is_superuser。
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user and user.is_authenticated and (user.is_staff or user.is_superuser)
        )

