from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Project, ProjectImage


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ("preview", "image", "caption_tr", "caption_en", "order")
    readonly_fields = ("preview",)

    @admin.display(description="önizleme")
    def preview(self, obj):
        if obj.pk and obj.thumb:
            return format_html('<img src="{}" style="height:64px;border-radius:8px">', obj.thumb.url)
        return "—"


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("idx", "title", "year", "featured", "is_published")
    list_display_links = ("idx", "title")
    list_editable = ("featured", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories",)
    inlines = [ProjectImageInline]
    fieldsets = (
        (None, {"fields": ("number", "title", "slug", "year", "categories", "stack", "featured", "is_published")}),
        ("Kısa bilgiler", {"fields": (("role_tr", "role_en"), ("duration_tr", "duration_en"), "repo_url", "live_url", "cover")}),
        ("Türkçe metin", {"fields": ("summary_tr", "problem_tr", "did_tr", "result_tr", "flow_tr")}),
        ("İngilizce metin", {"fields": ("summary_en", "problem_en", "did_en", "result_en", "flow_en"),
                             "description": "Boş bırakılan alanlarda İngilizce sayfada Türkçesi görünür."}),
    )

    @admin.display(description="no", ordering="number")
    def idx(self, obj):
        return obj.idx


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_tr", "name_en", "slug", "order")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name_tr",)}
