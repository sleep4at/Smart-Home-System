from django.contrib import admin

from .models import EmailAlertRule, SystemLog


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ["id", "level", "source", "message_short", "created_at"]
    list_filter = ["level", "source", "created_at"]
    search_fields = ["message", "source"]
    readonly_fields = ["level", "source", "message", "data", "user", "created_at"]

    def message_short(self, obj):
        return (obj.message or "")[:60]

    message_short.short_description = "消息"


@admin.register(EmailAlertRule)
class EmailAlertRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "enabled", "preset", "trigger_device", "trigger_field", "last_triggered_at"]
    list_filter = ["enabled", "preset"]
    search_fields = ["name", "recipients"]
