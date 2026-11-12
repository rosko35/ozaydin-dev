"""Giriş denemesi sınırı: aynı IP'den 15 dakikada 5 başarısız denemeden sonra 15 dakika bekletme.

Sayaç veritabanında tutulur (LocMemCache her gunicorn işçisinde ayrı olduğu için güvenilmez).
Engel varken yapılan denemeler hiç değerlendirilmez (doğru şifre bile geçmez) ve sayılmaz.
"""

from datetime import timedelta

from django.utils import timezone

from .models import LoginAttempt

WINDOW = timedelta(minutes=15)
LOCK = timedelta(minutes=15)
MAX_FAILURES = 5
KEEP = timedelta(days=1)

BLOCKED_MESSAGE = "Çok fazla deneme, 15 dakika sonra tekrar dene."


def request_ip(request):
    from contact.views import client_ip  # geç içe aktarma: uygulamalar yüklenirken döngü olmasın

    return client_ip(request) or "bilinmiyor"


def is_blocked(ip):
    return LoginAttempt.objects.filter(ip=ip, blocked_until__gt=timezone.now()).exists()


def record_failure(ip):
    now = timezone.now()
    attempt = LoginAttempt.objects.create(ip=ip)
    if LoginAttempt.objects.filter(ip=ip, created_at__gte=now - WINDOW).count() >= MAX_FAILURES:
        attempt.blocked_until = now + LOCK
        attempt.save(update_fields=["blocked_until"])
    LoginAttempt.objects.filter(created_at__lt=now - KEEP).delete()


def clear(ip):
    LoginAttempt.objects.filter(ip=ip).delete()
