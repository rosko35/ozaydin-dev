from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Post, PostImage, Tag


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    fields = ("preview", "image", "alt_tr", "alt_en", "md_code")
    readonly_fields = ("preview", "md_code")
    verbose_name_plural = "Yazı görselleri (kaydettikten sonra Markdown kodunu kopyalayıp gövdeye yapıştır)"

    @admin.display(description="önizleme")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" alt="" style="height:64px;border-radius:8px">', obj.image.url)
        return "—"

    @admin.display(description="Markdown kodu")
    def md_code(self, obj):
        if not (obj.pk and obj.image):
            return "Kaydedince burada görünür."
        # user-select:all → tek tıkla hepsi seçilir, Ctrl+C ile kopyalanır.
        return format_html(
            '<code style="user-select:all;-webkit-user-select:all;cursor:copy;display:block;white-space:pre-wrap;word-break:break-all" '
            'title="Tıkla, Ctrl+C">{}</code>{}',
            obj.markdown("tr"),
            format_html('<code style="user-select:all;-webkit-user-select:all;cursor:copy;display:block;margin-top:4px;'
                        'white-space:pre-wrap;word-break:break-all" title="İngilizce gövde için">{}</code>', obj.markdown("en"))
            if obj.alt_en else "",
        )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title_tr", "status", "published_at", "has_en")
    list_filter = ("status", "tags", "published_at")
    search_fields = ("title_tr", "title_en", "summary_tr", "body_tr", "body_en")
    date_hierarchy = "published_at"
    prepopulated_fields = {"slug": ("title_tr",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("cover_preview", "updated")
    inlines = [PostImageInline]
    actions = ["publish", "rerender"]
    fieldsets = (
        ("Genel", {"fields": ("slug", ("status", "published_at"), "tags", "related_project", "cover", "cover_preview", "updated")}),
        ("Türkçe", {"fields": ("title_tr", "summary_tr", "body_tr")}),
        ("İngilizce", {"fields": ("title_en", "summary_en", "body_en"),
                       "description": "Boş bırakılan alanlarda İngilizce sayfada Türkçesi görünür."}),
    )

    @admin.display(description="EN", boolean=True)
    def has_en(self, obj):
        return bool(obj.body_en.strip())

    @admin.display(description="kapak önizlemesi")
    def cover_preview(self, obj):
        if obj.pk and obj.cover:
            return format_html('<img src="{}" alt="" style="max-height:200px;max-width:100%;border-radius:12px">', obj.cover.url)
        return "—"

    @admin.action(description="Seçili yazıları yayına al")
    def publish(self, request, queryset):
        n = 0
        for post in queryset.exclude(status=Post.Status.PUBLISHED):
            post.status = Post.Status.PUBLISHED
            post.save()
            n += 1
        self.message_user(request, f"{n} yazı yayına alındı.", messages.SUCCESS)

    @admin.action(description="HTML'i yeniden üret (Markdown ayarları değiştiyse)")
    def rerender(self, request, queryset):
        for post in queryset:
            post.render_html()
            Post.objects.filter(pk=post.pk).update(body_html_tr=post.body_html_tr, body_html_en=post.body_html_en)
        self.message_user(request, f"{queryset.count()} yazı yeniden üretildi.", messages.SUCCESS)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name_tr", "name_en", "slug")
    search_fields = ("name_tr", "name_en")
    prepopulated_fields = {"slug": ("name_tr",)}
