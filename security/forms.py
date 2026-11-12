import re

from django import forms
from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

from . import throttle


def clean_token(value):
    """Boşluk ve tireleri at (yedek kodlar 'abcd-efgh' diye gösterilir), küçük harfe çevir."""
    return re.sub(r"[\s-]", "", value or "").lower()


class SecureAdminAuthenticationForm(AdminAuthenticationForm):
    """Admin giriş formu: IP başına deneme sınırı + (DJANGO_ADMIN_2FA=1 iken) doğrulama kodu.

    Kod alanına 6 haneli uygulama kodu ya da bir yedek kod yazılır; hangisi olduğu uzunluğundan anlaşılır.
    """

    otp_token = forms.CharField(
        label="Doğrulama kodu",
        required=False,
        widget=forms.TextInput(
            attrs={"autocomplete": "one-time-code", "autocapitalize": "off", "spellcheck": "false"}
        ),
    )

    blocked = False

    def clean(self):
        ip = throttle.request_ip(self.request)
        if throttle.is_blocked(ip):
            # Şifre hiç denenmez: engel varken doğru şifre bile geçmez.
            self.blocked = True
            raise ValidationError(throttle.BLOCKED_MESSAGE, code="blocked")

        cleaned = super().clean()  # kullanıcı adı/şifre; yanlışsa sinyal sayacı artırır
        user = self.get_user()
        if user is not None and settings.ADMIN_2FA:
            self._check_token(user, ip, cleaned.get("otp_token"))
        return cleaned

    def _check_token(self, user, ip, raw):
        token = clean_token(raw)
        if not token:
            raise ValidationError("Doğrulama kodunu da gir.", code="token_required")

        totp = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        static = StaticDevice.objects.filter(user=user, confirmed=True).first()
        device = None
        if token.isdigit() and len(token) == 6:
            device = totp
        elif len(token) == 8:
            device = static

        if device is not None:
            allowed, _extra = device.verify_is_allowed()
            if not allowed:
                throttle.record_failure(ip)
                raise ValidationError(
                    "Çok fazla hatalı kod girildi, bir süre bekleyip tekrar dene.", code="otp_throttled"
                )
            if device.verify_token(token):
                user.otp_device = device  # django_otp oturuma bunu yazar (giriş tamamlanınca)
                return

        throttle.record_failure(ip)
        raise ValidationError(
            "Doğrulama kodu hatalı ya da bu hesapta doğrulama cihazı kurulu değil.", code="invalid_token"
        )
