"""
Sitenin bütün dile bağlı adresleri tek yerde.

Her satır: (ad, Türkçe yol, İngilizce yol, görünüm). Türkçe adresler kökte (/projeler/),
İngilizceler /en/ altında (/en/projects/). Ad, şablonlarda {% lurl "ad" %} ile kullanılır.
"""
from django.urls import path, reverse
from django.utils.translation import get_language

from blog import views as blog_views
from contact import views as contact_views
from core import views as core_views
from projects import views as project_views

ROUTES = [
    ("home", "", "", core_views.home),
    ("projects", "projeler/", "projects/", project_views.project_list),
    ("project", "projeler/<slug:slug>/", "projects/<slug:slug>/", project_views.project_detail),
    ("blog", "blog/", "blog/", blog_views.post_list),
    ("blog_tag", "blog/etiket/<slug:slug>/", "blog/tag/<slug:slug>/", blog_views.tag_detail),
    ("blog_feed", "blog/rss/", "blog/rss/", blog_views.feed),
    ("post", "blog/<slug:slug>/", "blog/<slug:slug>/", blog_views.post_detail),
    ("about", "hakkimda/", "about/", core_views.about),
    ("contact", "iletisim/", "contact/", contact_views.contact),
]


def urlpatterns_for(lang):
    i = 1 if lang == "tr" else 2
    return [path(r[i], r[3], name=r[0]) for r in ROUTES]


def lreverse(name, lang=None, **kwargs):
    """Adı, verilen (ya da şu anki) dildeki adrese çevirir."""
    lang = lang or get_language() or "tr"
    return reverse(f"{lang}:{name}", kwargs=kwargs or None)


def alternates(name, **kwargs):
    """Aynı sayfanın iki dildeki adresi: {'tr': '/projeler/', 'en': '/en/projects/'}."""
    return {lang: lreverse(name, lang, **kwargs) for lang in ("tr", "en")}
