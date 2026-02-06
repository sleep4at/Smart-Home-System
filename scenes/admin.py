from django.contrib import admin

from .models import SceneRule


@admin.register(SceneRule)
class SceneRuleAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "enabled",
        "owner",
        "trigger_type",
        "trigger_device",
        "action_device",
        "created_at",
    ]
    list_filter = ["enabled", "trigger_type", "action_type", "created_at"]
    search_fields = ["name", "owner__username"]
    readonly_fields = ["created_at", "updated_at", "last_triggered_at"]
