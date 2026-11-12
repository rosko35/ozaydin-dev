from django.conf import settings

from . import seo
from .routes import alternates
from .translate import lang


def site(request):
    """Her şablonda: dil, diğer dildeki adres, site adresi."""
    match = getattr(request, "resolver_match", None)
    alt = {}
    if match and match.namespace in ("tr", "en"):
        try:
            alt = alternates(match.url_name, **match.kwargs)
        except Exception:
            alt = {}
    return {
        "lang": lang(),
        "other_lang": "en" if lang() == "tr" else "tr",
        "alt_urls": alt,
        "site_url": settings.SITE_URL.rstrip("/"),
        "chat_enabled": bool(settings.CHAT_API_KEY),
        "google_verification": settings.GOOGLE_SITE_VERIFICATION,
        **seo.context(request),  # og_image, canonical_url
    }
