"""Dilden bağımsız adresler: robots.txt, sitemap.xml, paylaşım görselleri (OG kartları), ikonlar."""
from django.contrib.sitemaps.views import sitemap
from django.urls import path, re_path

from chat import views as chat_views

from . import seo_views
from .sitemaps import SITEMAPS

LANG = r"(?P<lang>tr|en)"

urlpatterns = [
    path("api/chat/", chat_views.ask, name="chat_api"),
    path("robots.txt", seo_views.robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("site.webmanifest", seo_views.webmanifest, name="webmanifest"),
    path("favicon.ico", seo_views.favicon, name="favicon"),
    re_path(rf"^og/home-{LANG}\.png$", seo_views.og_home, name="og_home"),
    re_path(rf"^og/page/(?P<key>[a-z]+)-{LANG}\.png$", seo_views.og_page, name="og_page"),
    re_path(rf"^og/project/(?P<slug>[-a-zA-Z0-9_]+)-{LANG}\.png$", seo_views.og_project, name="og_project"),
    re_path(rf"^og/post/(?P<slug>[-a-zA-Z0-9_]+)-{LANG}\.png$", seo_views.og_post, name="og_post"),
]
