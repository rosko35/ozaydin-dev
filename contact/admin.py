from urllib.parse import quote

from django.contrib import admin
from django.utils.html import format_html

from .models import Message


def mailto(obj):
    return f"mailto:{obj.email}?subject={quote('Re: ozaydin.dev')}"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("read_mark", "name", "email", "short", "created", "lang", "reply")
    list_display_links = ("name", "short")
    list_filter = ("is_read", "is_spam", "lang")
    search_fields = ("name", "email", "body")
    date_hierarchy = "created"
    actions = ("mark_read", "mark_spam")
    fields = ("name", "email", "reply", "lang", "created", "body", "ip", "user_agent", "is_read", "is_spam", "emailed")
    readonly_fields = ("name", "email", "reply", "lang", "created", "body", "ip", "user_agent", "emailed")

    @admin.display(description="okundu", boolean=True, ordering="is_read")
    def read_mark(self, obj):
        return obj.is_read

    @admin.display(description="mesaj")
    def short(self, obj):
        text = " ".join(obj.body.split())
        return text if len(text) <= 60 else text[:60] + "…"

    @admin.display(description="yanıt")
    def reply(self, obj):
        return format_html('<a href="{}">Yanıtla</a>', mailto(obj))

    @admin.action(description="Seçilenleri okundu yap")
    def mark_read(self, request, queryset):
        n = queryset.update(is_read=True)
        self.message_user(request, f"{n} mesaj okundu olarak işaretlendi.")

    @admin.action(description="Seçilenleri spam olarak işaretle")
    def mark_spam(self, request, queryset):
        n = queryset.update(is_spam=True, is_read=True)
        self.message_user(request, f"{n} mesaj spam olarak işaretlendi.")

    def has_add_permission(self, request):
        return False

    def changelist_view(self, request, extra_context=None):
        unread = Message.objects.filter(is_read=False, is_spam=False).count()
        extra_context = {**(extra_context or {}), "title": f"Mesajlar · {unread} okunmamış" if unread else "Mesajlar · hepsi okundu"}
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if request.method == "GET" and str(object_id).isdigit():
            Message.objects.filter(pk=object_id, is_read=False).update(is_read=True)
        return super().change_view(request, object_id, form_url, extra_context)
