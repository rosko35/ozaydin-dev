from django.contrib import admin

from .models import ChatLog


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ("created", "lang", "short_q", "ok", "ms")
    list_filter = ("ok", "lang")
    search_fields = ("question", "answer")
    readonly_fields = ("created", "lang", "question", "answer", "ok", "error", "ms")
    exclude = ("ip_hash",)

    @admin.display(description="soru")
    def short_q(self, obj):
        return obj.question[:80]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
