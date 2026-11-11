"""
/sitemap.xml: her sayfanın Türkçe ve İngilizce hâli ayrı <url>, ikisi de xhtml:link ile birbirine bağlı.

Django'nun i18n sitemap'i her öğeyi her dilde, o dil etkinken location() ile üretir; bizim lreverse
etkin dili kullandığı için ayrı bir şey gerekmez. Alan adı ve protokol isteğe göre değil, SITE_URL'den
gelir (Sites uygulaması kullanılmıyor).
"""
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import Max

from projects.models import Project

from .routes import lreverse
from .seo import post_model


class BaseSitemap(Sitemap):
    i18n = True
    alternates = True
    languages = ["tr", "en"]

    def get_urls(self, page=1, site=None, protocol=None):
        parts = urlsplit(settings.SITE_URL)
        urls = self._urls(page, parts.scheme or "https", parts.netloc)
        for url in urls:
            # x-default: Türkçe hâli (kökteki adresler)
            tr = next((a["location"] for a in url["alternates"] if a["lang_code"] == "tr"), None)
            if tr:
                url["alternates"].append({"location": tr, "lang_code": "x-default"})
        return urls


def _latest_project():
    return Project.objects.filter(is_published=True).aggregate(m=Max("updated"))["m"]


def _latest_post():
    Post = post_model()
    if Post is None:
        return None
    return Post.objects.published().aggregate(m=Max("updated"))["m"]


class StaticSitemap(BaseSitemap):
    def items(self):
        return ["home", "projects", "blog", "about", "contact"]

    def location(self, item):
        return lreverse(item)

    def lastmod(self, item):
        if item == "projects":
            return _latest_project()
        if item == "blog":
            return _latest_post()
        if item == "home":
            return max(filter(None, [_latest_project(), _latest_post()]), default=None)
        return None


class ProjectSitemap(BaseSitemap):
    def items(self):
        return Project.objects.filter(is_published=True).order_by("number")

    def location(self, item):
        return lreverse("project", slug=item.slug)

    def lastmod(self, item):
        return item.updated


class PostSitemap(BaseSitemap):
    def items(self):
        Post = post_model()
        return Post.objects.published() if Post else []

    def location(self, item):
        return lreverse("post", slug=item.slug)

    def lastmod(self, item):
        return getattr(item, "updated", None) or getattr(item, "published_at", None)


SITEMAPS = {"pages": StaticSitemap, "projects": ProjectSitemap, "posts": PostSitemap}
