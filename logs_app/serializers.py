from rest_framework import serializers

from .models import SystemLog


class SystemLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemLog
        fields = [
            "id",
            "level",
            "source",
            "message",
            "data",
            "user",
            "created_at",
        ]
        read_only_fields = fields

