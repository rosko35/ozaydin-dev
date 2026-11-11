"""
SEO yardımcıları: kanonik adres, paylaşım görseli (OG kartı) adresi, yapılandırılmış veri (JSON-LD).

- context(request): her şablona `og_image` (bu sayfanın kartının mutlak adresi) ve `canonical_url` koyar.
  core.context.site içinden çağrılır.
- head(context): core/_meta.html'in kullandığı bütün değerler ({% seo_head as seo %}).

Blog uygulaması henüz yazılmamış olabilir: blog modeline her erişim post_model() üzerinden, korumalı.
"""
import json
from urllib.parse import urlencode

from django.apps import apps
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

from .routes import lreverse
from .translate import lang as current_lang
from .translate import tfield, ui

PAGE_KEYS = ("projects", "blog", "about", "contact")
OG_LOCALE = {"tr": "tr_TR", "en": "en_US"}

PERSON = {
    "name": "Emre Özaydın",
    "jobTitle": "Information Systems and Technologies Student",
    "alumniOf": {"@type": "CollegeOrUniversity", "name": "Yaşar University"},
    "affiliation": {"@type": "CollegeOrUniversity", "name": "Eastern Mediterranean University"},
    "sameAs": [
        "https://github.com/rosko35",
        "https://www.linkedin.com/in/emre-%C3%B6zayd%C4%B1n-b65409270/",
    ],
    "knowsLanguage": ["tr", "en", "es", "de"],
    "knowsAbout": ["Python", "Django", "C#", "Unity", "SQL", "JavaScript"],
}


def site_url():
    return settings.SITE_URL.rstrip("/")


def absolute(path):
    return site_url() + path


def post_model():
    """blog.models.Post, yayımlanmış yazıları veren `published()` ile birlikte hazırsa; değilse None."""
    if not apps.is_installed("blog"):
        return None
    try:
        from blog.models import Post
    except ImportError:
        return None
    if not hasattr(Post, "objects") or not hasattr(Post.objects, "published"):
        return None
    return Post


def route_of(request):
    """(adres adı, parametreler) — sadece dile bağlı sayfalarda (tr:/en:), diğerlerinde None."""
    match = getattr(request, "resolver_match", None)
    if match and match.namespace in ("tr", "en"):
        return match.url_name, match.kwargs
    return None


def og_path(name, kwargs, lang):
    """Bir sayfanın OG kartının yolu: /og/project/safe-city-tr.png gibi."""
    slug = (kwargs or {}).get("slug")
    if name == "project" and slug:
        return reverse("og_project", kwargs={"slug": slug, "lang": lang})
    if name == "post" and slug:
        return reverse("og_post", kwargs={"slug": slug, "lang": lang})
    if name == "blog_tag":
        name = "blog"
    if name in PAGE_KEYS:
        return reverse("og_page", kwargs={"key": name, "lang": lang})
    return reverse("og_home", kwargs={"lang": lang})


def og_image_url(request, obj=None):
    """Bu sayfanın kartının mutlak adresi. obj verilirse ?v=<güncelleme zamanı> eklenir:
    içerik değişince paylaşım sitelerinin önbelleği de yenilenir."""
    route = route_of(request)
    name, kwargs = route if route else ("home", {})
    url = absolute(og_path(name, kwargs, current_lang()))
    updated = getattr(obj, "updated", None)
    if updated:
        url += "?v=" + str(int(updated.timestamp()))
    return url


def canonical_url(request):
    """site adresi + yol. Sorgu parametreleri atılır; sadece ?page=N (N>1) korunur."""
    url = absolute(request.path)
    page = request.GET.get("page", "")
    if page.isdigit() and int(page) > 1:
        url += "?" + urlencode({"page": int(page)})
    return url


def context(request):
    return {"og_image": og_image_url(request), "canonical_url": canonical_url(request)}


# --- JSON-LD ---------------------------------------------------------------------------------------

def person_ref():
    return {"@id": site_url() + "/#person"}


def person():
    return {"@type": "Person", "@id": site_url() + "/#person", "url": site_url(), **PERSON}


def website(lang):
    return {
        "@type": "WebSite",
        "@id": site_url() + "/#website",
        "url": site_url() + "/",
        "name": "ozaydin.dev",
        "description": ui("site.description"),
        "inLanguage": lang,
        "author": person_ref(),
        "publisher": person_ref(),
    }


def breadcrumbs(items):
    """items: [(ad, mutlak adres), ...]"""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": url}
            for i, (name, url) in enumerate(items, start=1)
        ],
    }


def creative_work(project, url, image, lang):
    data = {
        "@type": "CreativeWork",
        "name": project.title,
        "description": tfield(project, "summary"),
        "url": url,
        "image": image,
        "inLanguage": lang,
        "author": person_ref(),
    }
    if project.year:
        data["dateCreated"] = str(project.year)
    if getattr(project, "updated", None):
        data["dateModified"] = project.updated.isoformat()
    if project.stack:
        data["keywords"] = ", ".join(s.strip() for s in project.stack.split("·") if s.strip())
    return data


def blog_posting(post, url, image, description, lang):
    data = {
        "@type": "BlogPosting",
        "headline": Truncator(tfield(post, "title")).chars(110),
        "description": description,
        "url": url,
        "image": [image],
        "inLanguage": lang,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "author": {"@type": "Person", "@id": site_url() + "/#person", "name": PERSON["name"], "url": site_url()},
        "publisher": person_ref(),
    }
    published = getattr(post, "published_at", None)
    updated = getattr(post, "updated", None)
    if published:
        data["datePublished"] = published.isoformat()
    if updated or published:
        data["dateModified"] = (updated or published).isoformat()
    return data


def jsonld(data):
    """<script type="application/ld+json"> içine güvenle konabilen JSON (</script> kapanamaz)."""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    text = text.replace("<", "\\u003C").replace(">", "\\u003E").replace("&", "\\u0026")
    return mark_safe(text)


# --- <head> için hepsi bir arada --------------------------------------------------------------------

def head(ctx):
    request = ctx.get("request")
    lang = current_lang()
    page_key = ctx.get("page_key", "")
    article = ctx.get("article")
    project = ctx.get("project") if page_key == "project" else None
    noindex = bool(ctx.get("noindex")) or page_key == "404"

    title = f"{ctx['page_title']} · ozaydin.dev" if ctx.get("page_title") else ui("site.title")
    desc = ctx.get("page_description") or ""
    desc = Truncator(" ".join(strip_tags(str(desc)).split())).chars(160) if desc else ui("site.description")

    obj = article or project
    image = og_image_url(request, obj) if request else ""
    canonical = canonical_url(request) if request and not noindex else ""
    shown = tfield(article, "title") if article else (project.title if project else (ctx.get("page_title") or ""))
    image_alt = f"{shown} · Emre Özaydın" if shown else "Emre Özaydın · ozaydin.dev"

    graph = [website(lang), person()]
    if project is not None and canonical:
        graph.append(creative_work(project, canonical, image, lang))
        graph.append(breadcrumbs([
            (ui("nav.home_long"), absolute(lreverse("home"))),
            (ui("nav.projects"), absolute(lreverse("projects"))),
            (project.title, canonical),
        ]))
    if article is not None and canonical:
        graph.append(blog_posting(article, canonical, image, desc, lang))
        graph.append(breadcrumbs([
            (ui("nav.home_long"), absolute(lreverse("home"))),
            (ui("nav.blog"), absolute(lreverse("blog"))),
            (tfield(article, "title"), canonical),
        ]))

    published = getattr(article, "published_at", None) if article else None
    modified = (getattr(article, "updated", None) or published) if article else None
    return {
        "title": title,
        "description": desc,
        "canonical": canonical,
        "noindex": noindex,
        "og_type": "article" if article else "website",
        "image": image,
        "image_alt": image_alt,
        "locale": OG_LOCALE[lang],
        "locale_alt": OG_LOCALE["en" if lang == "tr" else "tr"],
        "published": published.isoformat() if published else "",
        "modified": modified.isoformat() if modified else "",
        "jsonld": jsonld({"@context": "https://schema.org", "@graph": graph}),
    }
