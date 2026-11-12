import hashlib
import json
import logging
import time
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from contact.views import client_ip
from core.translate import ui

from . import providers
from .knowledge import system_prompt
from .models import ChatLog

log = logging.getLogger(__name__)

MAX_CHARS = 500       # bir sorunun en fazla uzunluğu
MAX_TURNS = 6         # modele gönderilen en fazla önceki mesaj
PER_HOUR = 10         # kişi başı saatlik soru
PER_DAY = 30          # kişi başı günlük soru
SITE_PER_DAY = 200    # bütün site, günlük
KEEP_DAYS = 30        # kayıtlar kaç gün saklanır


def enabled():
    return bool(settings.CHAT_PROVIDER in providers.PROVIDERS and settings.CHAT_API_KEY)


def _ip_hash(request):
    ip = client_ip(request) or "?"
    return hashlib.sha256((settings.SECRET_KEY + ip).encode()).hexdigest()


def _same_origin(request):
    origin = request.headers.get("Origin") or request.headers.get("Referer") or ""
    if not origin:
        return False
    host = urlparse(origin).netloc
    return host == request.get_host()


def _err(key, status, lang):
    from django.utils import translation

    with translation.override(lang):
        return JsonResponse({"ok": False, "message": ui(key)}, status=status)


@csrf_exempt  # JSON uç noktası; CSRF yerine aynı site kontrolü (Origin) ve JSON gövdesi şartı var.
@require_POST
def ask(request):
    try:
        data = json.loads(request.body.decode() or "{}")
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False}, status=400)
    lang = "en" if data.get("lang") == "en" else "tr"
    if not _same_origin(request) or request.content_type != "application/json":
        return JsonResponse({"ok": False}, status=403)
    if not enabled():
        return _err("chat.off", 503, lang)

    question = " ".join(str(data.get("message", "")).split())[:MAX_CHARS]
    if not question:
        return _err("chat.empty", 400, lang)

    now = timezone.now()
    ChatLog.objects.filter(created__lt=now - timedelta(days=KEEP_DAYS)).delete()
    h = _ip_hash(request)
    mine = ChatLog.objects.filter(ip_hash=h)
    if mine.filter(created__gte=now - timedelta(hours=1)).count() >= PER_HOUR or \
            mine.filter(created__gte=now - timedelta(days=1)).count() >= PER_DAY:
        return _err("chat.limit", 429, lang)
    if ChatLog.objects.filter(created__gte=now - timedelta(days=1)).count() >= SITE_PER_DAY:
        return _err("chat.busy", 429, lang)

    history = []
    for m in (data.get("history") or [])[-MAX_TURNS:]:
        if isinstance(m, dict) and m.get("role") in ("user", "bot") and isinstance(m.get("text"), str):
            history.append({"role": m["role"], "text": m["text"][:1500]})
    while history and history[0]["role"] != "user":  # konuşma kullanıcıyla başlamalı
        history.pop(0)
    history.append({"role": "user", "text": question})

    entry = ChatLog(lang=lang, ip_hash=h, question=question)
    t0 = time.monotonic()
    try:
        answer = providers.ask(system_prompt(), history)
        entry.answer = answer
    except providers.ProviderError as e:
        log.warning("Asistan cevap veremedi: %s", e)
        entry.ok, entry.error = False, str(e)[:200]
        answer = None
    entry.ms = int((time.monotonic() - t0) * 1000)
    entry.save()
    if answer is None:
        return _err("chat.error", 502, lang)
    return JsonResponse({"ok": True, "answer": answer})
