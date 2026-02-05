from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .permissions import IsAdminUserRole
from .serializers import MeSerializer, UserSerializer


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


class MeView(RetrieveAPIView):
    """
    返回当前登录用户信息，供前端判断是否管理员等。
    """

    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

