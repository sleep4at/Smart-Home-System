from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    管理员管理用户用的序列化器。
    """

    password = serializers.CharField(write_only=True, required=False)
    is_admin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_admin",
            "password",
        ]
        read_only_fields = ["id", "is_superuser", "is_admin"]

    def get_is_admin(self, obj) -> bool:
        return bool(obj.is_staff or obj.is_superuser)

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class MeSerializer(serializers.ModelSerializer):
    """
    返回当前登录用户自己的信息。
    """

    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_admin",
        ]

    def get_is_admin(self, obj) -> bool:
        return bool(obj.is_staff or obj.is_superuser)

