from django.conf import settings
from django.contrib.admin import AdminSite
from django.urls import path
from django_otp.plugins.otp_totp.models import TOTPDevice

from .forms import SecureAdminAuthenticationForm


class SecureAdminSite(AdminSite):
    """Varsayılan admin sitesi: deneme sınırlı giriş, isteğe bağlı (DJANGO_ADMIN_2FA=1) doğrulama kodu zorunluluğu
    ve <ADMIN_URL>2fa/ kurulum sayfası."""

    login_form = SecureAdminAuthenticationForm
    login_template = "security/login.html"

    def has_permission(self, request):
        if not super().has_permission(request):
            return False
        if settings.ADMIN_2FA:
            # OTPMiddleware'in koyduğu: oturum, doğrulanmış (onaylı) bir cihazla açıldıysa True
            return bool(getattr(request.user, "is_verified", lambda: False)())
        return True

    def get_urls(self):
        from . import views

        custom = [path("2fa/", self.admin_view(views.two_factor_view), name="security_2fa")]
        return custom + super().get_urls()

    def login(self, request, extra_context=None):
        context = {"two_factor_required": settings.ADMIN_2FA, **(extra_context or {})}
        response = super().login(request, context)
        form = getattr(response, "context_data", {}).get("form") if hasattr(response, "context_data") else None
        if form is not None and getattr(form, "blocked", False):
            response.status_code = 429
            response["Retry-After"] = "900"
        return response

    def index(self, request, extra_context=None):
        has_device = TOTPDevice.objects.filter(user=request.user, confirmed=True).exists()
        context = {
            "two_factor_missing": not has_device,
            "two_factor_not_enforced": has_device and not settings.ADMIN_2FA,
            **(extra_context or {}),
        }
        return super().index(request, context)
