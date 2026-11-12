import datetime
import hashlib
import logging
import re
from urllib.parse import urlsplit

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .models import DailyPage, DailyReferrer, DailyVisitor

logger = logging.getLogger(__name__)

BOT_RE = re.compile(
    r"bot|crawl|spider|slurp|facebookexternalhit|preview|lighthouse|headless|curl|wget|"
    r"python-requests|python-urllib|httpx|go-http|okhttp|java/|libwww|scrapy|monitor|uptime|pingdom|"
    r"axios|node-fetch|postman|phantomjs",
    re.I,
)
SKIP_PREFIXES = ("/static/", "/media/", "/og/", "/api/", "/sitemap", "/robots.txt", "/favicon")
_last_cleanup = {"date": None}


def _upsert(model, lookup, inc, defaults):
    """Satırı tek UPDATE ile artır (inc: {alan: miktar}); yoksa oluştur (yarışta tekrar UPDATE)."""
    bump = {f: F(f) + n for f, n in inc.items()}
    if model.objects.filter(**lookup).update(**bump):
        return
    try:
        with transaction.atomic():
            model.objects.create(**lookup, **defaults)
    except IntegrityError:
        model.objects.filter(**lookup).update(**bump)


def _client_ip(request):
    from contact.views import client_ip

    return client_ip(request) or request.META.get("REMOTE_ADDR", "")


def should_count(request, response):
    if request.method != "GET" or response.status_code != 200:
        return False
    if not response.headers.get("Content-Type", "").startswith("text/html"):
        return False
    path = request.path
    if path.startswith(SKIP_PREFIXES) or path.startswith("/" + settings.ADMIN_URL.lstrip("/")):
        return False
    if request.META.get("HTTP_DNT") == "1" or request.META.get("HTTP_SEC_GPC") == "1":
        return False
    ua = request.META.get("HTTP_USER_AGENT", "")
    return bool(ua) and not BOT_RE.search(ua)


def referrer_host(request):
    ref = request.META.get("HTTP_REFERER", "")
    if not ref:
        return ""
    try:
        host = (urlsplit(ref).hostname or "").lower().removeprefix("www.")
    except ValueError:
        return ""
    own = {request.get_host().split(":")[0].lower().removeprefix("www.")}
    site_host = urlsplit(settings.SITE_URL).hostname
    if site_host:
        own.add(site_host.lower().removeprefix("www."))
    return "" if not host or host in own else host[:200]


def record(request):
    today = timezone.localdate()
    ua = request.META.get("HTTP_USER_AGENT", "")
    digest = hashlib.sha256(f"{settings.SECRET_KEY}|{today}|{_client_ip(request)}|{ua}".encode()).hexdigest()
    is_new = False
    try:
        with transaction.atomic():
            DailyVisitor.objects.create(date=today, hash=digest)
        is_new = True
    except IntegrityError:
        pass
    path = request.path[:200]
    lang = getattr(request, "LANGUAGE_CODE", "tr")[:2]
    new = 1 if is_new else 0
    _upsert(DailyPage, {"date": today, "path": path}, {"views": 1, "unique": new}, {"lang": lang, "views": 1, "unique": new})
    if is_new:
        host = referrer_host(request)
        if host:
            _upsert(DailyReferrer, {"date": today, "host": host}, {"count": 1}, {"count": 1})
    if _last_cleanup["date"] != today:
        _last_cleanup["date"] = today
        DailyVisitor.objects.filter(date__lt=today - datetime.timedelta(days=1)).delete()


class CountPageView:
    """Çerezsiz sayaç. pjax (X-Requested-With: pjax) geçişleri de gerçek sayfa görüntülemesidir."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if should_count(request, response):
                record(request)
        except Exception:
            logger.exception("İstatistik kaydedilemedi")
        return response
