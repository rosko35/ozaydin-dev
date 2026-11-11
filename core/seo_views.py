"""Dilden bağımsız SEO adresleri: OG kartları, robots.txt, site.webmanifest, /favicon.ico."""
import hashlib
import json
import os
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect
from django.templatetags.static import static
from django.utils import translation
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from projects.models import Project

from .og import render as og
from .seo import post_model
from .translate import tfield, ui

PAGE_INDEX = {"projects": 1, "blog": 2, "about": 3, "contact": 4}


def _card_response(kind, key, lang, spec):
    """Kartı MEDIA_ROOT/og/ altında önbellekten verir; yoksa (ya da metin/tasarım değiştiyse) üretir.
    Dosya adındaki özet, çizilen her şeyden hesaplanır: başlık değişince yeni dosya üretilir."""
    digest = hashlib.sha1(repr((og.VERSION, sorted(spec.items()))).encode()).hexdigest()[:12]
    folder = Path(settings.MEDIA_ROOT) / "og"
    prefix = f"{kind}-{key}-{lang}-"
    path = folder / f"{prefix}{digest}.png"
    if not path.exists():
        data = og.render(**spec)
        try:
            folder.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(f".{os.getpid()}.tmp")
            tmp.write_bytes(data)
            os.replace(tmp, path)
            for old in folder.glob(f"{prefix}*.png"):
                if old != path:
                    old.unlink(missing_ok=True)
        except OSError:
            # Diske yazılamıyorsa (izin vb.) kartı yine de ver.
            response = HttpResponse(data, content_type="image/png")
            response["Cache-Control"] = "public, max-age=86400"
            return response
    response = FileResponse(open(path, "rb"), content_type="image/png")
    response["Cache-Control"] = "public, max-age=86400"
    return response


@require_GET
def og_home(request, lang):
    with translation.override(lang):
        spec = {"title": ui("og.home"), "label": "ozaydin.dev · 0b01", "tape_text": "ozaydin.dev"}
    return _card_response("home", "home", lang, spec)


@require_GET
def og_page(request, key, lang):
    if key not in PAGE_INDEX:
        raise Http404
    with translation.override(lang):
        spec = {"title": ui(f"{key}.title"), "label": f"ozaydin.dev · {PAGE_INDEX[key]:03b}"}
    return _card_response("page", key, lang, spec)


@require_GET
def og_project(request, slug, lang):
    project = Project.objects.filter(slug=slug, is_published=True).first()
    if project is None:
        raise Http404
    with translation.override(lang):
        spec = {"title": project.title, "label": f"ozaydin.dev · {project.idx}", "kind": ui("og.kind_project")}
    return _card_response("project", slug, lang, spec)


@require_GET
def og_post(request, slug, lang):
    Post = post_model()
    post = Post.objects.published().filter(slug=slug).first() if Post else None
    if post is None:
        raise Http404
    with translation.override(lang):
        date = getattr(post, "published_at", None)
        spec = {
            "title": tfield(post, "title"),
            "label": "ozaydin.dev" + (f" · {date:%Y-%m-%d}" if date else ""),
            "kind": ui("og.kind_post"),
        }
    return _card_response("post", slug, lang, spec)


@require_GET
@cache_control(public=True, max_age=86400)
def robots_txt(request):
    lines = ["User-agent: *"]
    # Yönetim paneli adresi gizli tutulabilsin diye (DJANGO_ADMIN_URL) sadece varsayılan adres yazılır:
    # robots.txt herkese açıktır, gizli adresi burada ilan etmek onu boşa çıkarır.
    if settings.ADMIN_URL.strip("/") == "admin":
        lines.append("Disallow: /admin/")
    else:
        lines.append("Disallow:")
    lines += ["", f"Sitemap: {settings.SITE_URL.rstrip('/')}/sitemap.xml", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@require_GET
@cache_control(public=True, max_age=86400)
def webmanifest(request):
    data = {
        "name": "Emre Özaydın · ozaydin.dev",
        "short_name": "ozaydin.dev",
        "description": ui("site.description"),
        "lang": "tr",
        "start_url": "/",
        "scope": "/",
        "display": "browser",
        "theme_color": "#02040A",
        "background_color": "#02040A",
        "icons": [
            {"src": static("core/icons/icon-192.png"), "sizes": "192x192", "type": "image/png"},
            {"src": static("core/icons/icon-512.png"), "sizes": "512x512", "type": "image/png"},
            {"src": static("core/icons/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    return HttpResponse(json.dumps(data, ensure_ascii=False, indent=2), content_type="application/manifest+json")


@require_GET
def favicon(request):
    # Yayında Nginx bu dosyayı doğrudan verir; bu yönlendirme bilgisayarda ve yedek olarak çalışır.
    return redirect(static("core/icons/favicon.ico"), permanent=False)
