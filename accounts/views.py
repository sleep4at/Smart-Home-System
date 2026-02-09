from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .permissions import IsAdminUserRole
from .serializers import MeSerializer, MeUpdateSerializer, UserSerializer


User = get_user_model()


class UserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    用户管理：只允许管理员访问。
    """

    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & IsAdminUserRole]


class MeView(RetrieveUpdateAPIView):
    """
    当前用户信息：GET 返回资料，PATCH 允许修改邮箱与密码。
    """

    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return MeUpdateSerializer
        return MeSerializer

