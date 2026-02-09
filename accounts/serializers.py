import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


User = get_user_model()

# Django 内置密码校验器的英文提示 -> 中文（与 manage.py changepassword 一致）
def _password_validation_message_zh(message: str) -> str:
    msg = message.strip()
    if "too short" in msg.lower():
        n = re.search(r"at least (\d+)", msg, re.I)
        return f"密码过短，至少需要 {n.group(1) if n else 8} 个字符。"
    if "too similar" in msg.lower():
        return "密码与用户名、邮箱等信息过于相似。"
    if "too common" in msg.lower():
        return "该密码过于常见，请换一个。"
    if "entirely numeric" in msg.lower():
        return "密码不能全是数字。"
    return msg


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


class MeUpdateSerializer(serializers.ModelSerializer):
    """
    当前用户修改自己的资料：仅允许修改邮箱与密码。
    修改密码时需提供原密码，新密码与 manage.py changepassword 使用相同校验规则。
    """

    current_password = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["email", "current_password", "password"]

    def validate(self, attrs):
        new_password = attrs.get("password")
        current_password = attrs.get("current_password")
        if new_password:
            if not current_password:
                raise serializers.ValidationError(
                    {"current_password": ["修改密码前请输入原密码。"]}
                )
            user = self.instance
            if not user.check_password(current_password):
                raise serializers.ValidationError(
                    {"current_password": ["原密码错误。"]}
                )
            try:
                validate_password(new_password, user)
            except DjangoValidationError as e:
                raw = getattr(e, "messages", None) or [str(e)]
                if isinstance(raw, str):
                    raw = [raw]
                messages = [_password_validation_message_zh(m) for m in raw]
                raise serializers.ValidationError({"password": messages})
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop("current_password", None)
        password = validated_data.pop("password", None)
        if "email" in validated_data:
            instance.email = validated_data["email"]
        if password:
            instance.set_password(password)
        instance.save()
        return instance

