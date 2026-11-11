"""
İletişim sayfası ve formu.

Spam koruması (CAPTCHA yok):
  - gizli tuzak alan "website" doluysa bot sayılır, sessizce "tamam" denir, kaydedilmez;
  - "ts" alanı sayfa açılırken imzalanan zaman damgasıdır; imza bozuksa, form 3 saniyeden hızlı
    gönderildiyse ya da 1 günden eskiyse yine sessizce "tamam" denir, kaydedilmez;
  - aynı IP'den son 1 saatte 5 mesaj varsa 429 döner;
  - mesajda 3'ten fazla link varsa kaydedilir ama spam işaretlenir, e-posta gitmez.
"""
import ipaddress
import logging
import re
import time
from datetime import timedelta

from django import forms
from django.conf import settings
from django.core import signing
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime

from core.translate import lang, ui

from .models import Message

log = logging.getLogger(__name__)

TS_SALT = "contact.form.ts"
MIN_SECONDS = 3
MAX_AGE = 24 * 60 * 60
RATE_LIMIT = 5  # son 1 saatte aynı IP'den en fazla bu kadar mesaj
MAX_LINKS = 3
LINK_RE = re.compile(r"https?://|www\.", re.I)
SENT_PARAM = "gonderildi"


def make_ts():
    """Şu anki zamanı imzalar; forma gizli alan olarak konur."""
    return signing.TimestampSigner(salt=TS_SALT).sign(str(int(time.time())))


def ts_ok(value):
    """İmza geçerli mi, form en az 3 sn önce ve en fazla 1 gün önce mi açılmış?"""
    try:
        started = int(signing.TimestampSigner(salt=TS_SALT).unsign(value or "", max_age=MAX_AGE))
    except (signing.BadSignature, ValueError):
        return False
    return time.time() - started >= MIN_SECONDS


def client_ip(request):
    """Ziyaretçinin IP'si. X-Forwarded-For'a sadece istek Nginx'ten (yerel adres/unix soket) geldiyse güvenilir."""
    remote = request.META.get("REMOTE_ADDR", "")
    try:
        trusted_proxy = ipaddress.ip_address(remote).is_loopback
    except ValueError:
        trusted_proxy = True  # unix soket: REMOTE_ADDR boş ya da IP değil
    candidate = remote
    if trusted_proxy:
        candidate = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or remote
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


class ContactForm(forms.Form):
    name = forms.CharField(min_length=1, max_length=100)
    email = forms.EmailField(max_length=200)
    message = forms.CharField(min_length=10, max_length=5000)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        f = self.fields
        f["name"].error_messages.update(required=ui("contact.err.name_required"), max_length=ui("contact.err.name_long", n=100))
        f["email"].error_messages.update(
            required=ui("contact.err.email_required"),
            invalid=ui("contact.err.email_invalid"),
            max_length=ui("contact.err.email_long", n=200),
        )
        f["message"].error_messages.update(
            required=ui("contact.err.message_required"),
            min_length=ui("contact.err.message_short", n=10),
            max_length=ui("contact.err.message_long", n=5000),
        )

    def first_errors(self):
        return {name: str(errs[0]) for name, errs in self.errors.items()}


def notify(msg):
    """Emre'ye düz metin bildirim. Hata olursa mesaj kaybolmaz: loglanır, emailed=False kalır."""
    admin_link = settings.SITE_URL.rstrip("/") + reverse("admin:contact_message_change", args=[msg.pk])
    body = "\n".join([
        f"Ad: {msg.name}",
        f"E-posta: {msg.email}",
        f"Dil: {msg.get_lang_display()}",
        f"Tarih: {localtime(msg.created):%d.%m.%Y %H:%M}",
        "",
        msg.body,
        "",
        "--",
        f"Admin'de aç: {admin_link}",
    ])
    email = EmailMessage(
        subject=f"ozaydin.dev · yeni mesaj: {msg.name}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_TO],
        reply_to=[msg.email],
    )
    try:
        email.send(fail_silently=False)
    except Exception:
        log.exception("İletişim bildirimi gönderilemedi (mesaj #%s kaydedildi)", msg.pk)
        return False
    Message.objects.filter(pk=msg.pk).update(emailed=True)
    return True


def page(request, *, status=200, values=None, errors=None, note=None, note_ok=False):
    ctx = {
        "page_key": "contact",
        "page_title": ui("contact.title"),
        "form_ts": make_ts(),
        "values": values or {},
        "errors": errors or {},
        "note": note,
        "note_ok": note_ok,
    }
    return render(request, "contact/contact.html", ctx, status=status)


def contact(request):
    if request.method != "POST":
        sent = request.GET.get(SENT_PARAM) == "1"
        return page(request, note=ui("contact.ok") if sent else None, note_ok=sent)

    is_fetch = request.headers.get("X-Requested-With") == "fetch"

    def success():
        if is_fetch:
            return JsonResponse({"ok": True, "message": ui("contact.ok"), "errors": {}})
        from core.routes import lreverse  # core.routes bu modülü içe aktarır; döngüye girmemek için burada

        return redirect(lreverse("contact") + f"?{SENT_PARAM}=1")

    def failure(message, errors=None, status=400):
        if is_fetch:
            return JsonResponse({"ok": False, "message": message, "errors": errors or {}}, status=status)
        values = {k: request.POST.get(k, "") for k in ("name", "email", "message")}
        return page(request, status=status, values=values, errors=errors, note=message)

    # (a) tuzak alan, (b) zaman damgası: bot sayılır, bota bir şey belli etme.
    if request.POST.get("website", "").strip() or not ts_ok(request.POST.get("ts")):
        return success()

    # (c) hız sınırı
    ip = client_ip(request)
    if ip and Message.objects.filter(ip=ip, created__gte=timezone.now() - timedelta(hours=1)).count() >= RATE_LIMIT:
        return failure(ui("contact.too_many"), status=429)

    form = ContactForm(request.POST)
    if not form.is_valid():
        return failure(ui("contact.fix"), form.first_errors())

    data = form.cleaned_data
    msg = Message.objects.create(
        name=data["name"],
        email=data["email"],
        body=data["message"],
        lang=lang(),
        ip=ip,
        user_agent=request.headers.get("User-Agent", "")[:300],
        is_spam=len(LINK_RE.findall(data["message"])) > MAX_LINKS,  # (d)
    )
    if not msg.is_spam:
        notify(msg)
    return success()
