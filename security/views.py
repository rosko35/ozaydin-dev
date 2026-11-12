import base64
from io import BytesIO

import django_otp
import qrcode
import qrcode.image.svg
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from . import throttle
from .forms import clean_token

BACKUP_CODE_COUNT = 10
DEVICE_NAME = "Telefon"


def make_backup_codes(user):
    """Eski yedek kodları siler, 10 yenisini üretir. Kodlar sadece bir kere gösterilir."""
    device, _ = StaticDevice.objects.get_or_create(user=user, name="Yedek kodlar", defaults={"confirmed": True})
    if not device.confirmed:
        device.confirmed = True
        device.save(update_fields=["confirmed"])
    device.token_set.all().delete()
    codes = []
    while len(codes) < BACKUP_CODE_COUNT:
        code = StaticToken.random_token()
        if code not in codes:
            codes.append(code)
    StaticToken.objects.bulk_create([StaticToken(device=device, token=c) for c in codes])
    return [f"{c[:4]}-{c[4:]}" for c in codes]


def qr_data(url):
    """otpauth adresini sunucuda SVG QR koduna çevirir (harici istek yok); <img src="data:..."> için base64."""
    image = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    buffer = BytesIO()
    image.save(buffer)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _password_ok(request):
    """Şifre onayı. Yanlış şifre giriş denemesi gibi sayılır; engel varken hiç denenmez."""
    ip = throttle.request_ip(request)
    if throttle.is_blocked(ip):
        messages.error(request, throttle.BLOCKED_MESSAGE)
        return False
    if request.user.check_password(request.POST.get("password", "")):
        return True
    throttle.record_failure(ip)
    messages.error(request, "Şifre yanlış.")
    return False


@never_cache
def two_factor_view(request):
    user = request.user
    if not user.is_superuser:
        raise PermissionDenied

    context = {
        **admin.site.each_context(request),
        "title": "İki adımlı doğrulama",
        "subtitle": None,
        "enforced": settings.ADMIN_2FA,
    }

    device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
    action = request.POST.get("action") if request.method == "POST" else None

    if device is not None:
        if action == "new_codes" and _password_ok(request):
            context.update(state="codes", codes=make_backup_codes(user))
            return TemplateResponse(request, "security/two_factor.html", context)
        if action == "reset":
            if settings.ADMIN_2FA:
                messages.error(
                    request,
                    "Doğrulama zorunluyken cihaz sıfırlanamaz (kilitlenirdin). "
                    "Sunucudaki DJANGO_ADMIN_2FA değerini 0 yapıp tekrar dene.",
                )
            elif _password_ok(request):
                TOTPDevice.objects.filter(user=user).delete()
                StaticDevice.objects.filter(user=user).delete()
                messages.success(request, "Cihaz sıfırlandı. Aşağıdan yenisini kurabilirsin.")
                return redirect(reverse("admin:security_2fa"))
        if action is not None:
            return redirect(reverse("admin:security_2fa"))

        context.update(
            state="ready",
            backup_left=sum(d.token_set.count() for d in StaticDevice.objects.filter(user=user, confirmed=True)),
        )
        return TemplateResponse(request, "security/two_factor.html", context)

    # Henüz onaylı cihaz yok: bekleyen (onaysız) cihazı kullan, yoksa yeni üret. Yenileyince QR aynı kalır.
    pending = TOTPDevice.objects.filter(user=user, confirmed=False).first()
    if pending is None:
        pending = TOTPDevice.objects.create(user=user, name=DEVICE_NAME, confirmed=False)

    error = None
    if action == "confirm":
        ip = throttle.request_ip(request)
        token = clean_token(request.POST.get("token"))
        if throttle.is_blocked(ip):
            error = throttle.BLOCKED_MESSAGE
        elif token.isdigit() and len(token) == 6 and pending.verify_token(token):
            pending.confirmed = True
            pending.save(update_fields=["confirmed"])
            django_otp.login(request, pending)  # bu oturum da doğrulanmış sayılsın
            context.update(state="codes", codes=make_backup_codes(user), just_enabled=True)
            return TemplateResponse(request, "security/two_factor.html", context)
        else:
            throttle.record_failure(ip)
            error = "Kod hatalı. Uygulamadaki 6 haneli güncel kodu yaz."

    context.update(
        state="setup",
        error=error,
        qr=qr_data(pending.config_url),
        secret=base64.b32encode(pending.bin_key).decode("ascii"),
    )
    return TemplateResponse(request, "security/two_factor.html", context)
