import datetime

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from .models import DailyPage, DailyReferrer

DAYS = 30


def bar_chart(days, values, width=720, height=140):
    """Sunucuda üretilen basit SVG çubuk grafik (gri tonlar, JS yok)."""
    top = max(values) or 1
    slot = width / len(values)
    bars = []
    for i, (day, v) in enumerate(zip(days, values)):
        h = round((height - 20) * v / top, 1) if v else 1
        x = round(i * slot + 1, 1)
        bars.append(
            f'<rect x="{x}" y="{round(height - 16 - h, 1)}" width="{round(slot - 2, 1)}" height="{h}" '
            f'rx="2" fill="{"#d4d4d8" if v else "#52525b"}"><title>{day:%d.%m.%Y}: {v}</title></rect>'
        )
    axis = (
        f'<text x="0" y="{height - 3}" font-size="10" fill="#a1a1aa">{days[0]:%d.%m}</text>'
        f'<text x="{width}" y="{height - 3}" font-size="10" fill="#a1a1aa" text-anchor="end">{days[-1]:%d.%m}</text>'
    )
    return mark_safe(
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Günlük görüntüleme" '
        f'style="width:100%;height:auto;background:#18181b;border-radius:8px">{"".join(bars)}{axis}</svg>'
    )


def build_summary():
    today = timezone.localdate()
    start = today - datetime.timedelta(days=DAYS - 1)
    pages = DailyPage.objects.filter(date__gte=start)
    per_day = {r["date"]: r for r in pages.values("date").annotate(v=Sum("views"), u=Sum("unique"))}
    days = [start + datetime.timedelta(days=i) for i in range(DAYS)]
    series = [per_day.get(d, {}).get("v") or 0 for d in days]
    total_views = sum(series)
    total_unique = sum(per_day.get(d, {}).get("u") or 0 for d in days)
    top_pages = list(pages.values("path").annotate(v=Sum("views")).order_by("-v")[:10])
    referrers = list(
        DailyReferrer.objects.filter(date__gte=start).values("host").annotate(c=Sum("count")).order_by("-c")[:10]
    )
    langs = {r["lang"]: r["v"] for r in pages.values("lang").annotate(v=Sum("views"))}
    tr, en = langs.get("tr", 0), langs.get("en", 0)
    share = round(100 * tr / (tr + en)) if tr + en else 0
    return {
        "days": DAYS,
        "total_views": total_views,
        "total_unique": total_unique,
        "chart": bar_chart(days, series),
        "top_pages": top_pages,
        "referrers": referrers,
        "tr": tr,
        "en": en,
        "tr_share": share,
        "en_share": 100 - share if tr + en else 0,
    }


@admin.register(DailyPage)
class DailyPageAdmin(admin.ModelAdmin):
    list_display = ("date", "path", "views", "unique")
    list_filter = ("date", "lang")
    search_fields = ("path",)
    ordering = ("-date", "-views")
    change_list_template = "admin/stats/dailypage/change_list.html"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        custom = path("istatistik/", staff_member_required(self.admin_site.admin_view(self.summary_view)), name="stats_summary")
        return [custom] + super().get_urls()

    def summary_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            "title": "İstatistik",
            "opts": self.model._meta,
            **build_summary(),
        }
        return TemplateResponse(request, "stats/summary.html", context)

    def changelist_view(self, request, extra_context=None):
        extra_context = {**(extra_context or {}), "summary_url": reverse("admin:stats_summary")}
        return super().changelist_view(request, extra_context)
