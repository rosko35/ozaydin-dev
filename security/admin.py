from django.contrib import admin

from .models import LoginAttempt


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Sadece okunur: saldırı denemelerini görmek için."""

    list_display = ("ip", "created_at", "blocked_until")
    list_filter = ("created_at",)
    search_fields = ("ip",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
