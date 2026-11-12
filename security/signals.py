from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from . import throttle


@receiver(user_login_failed)
def on_login_failed(sender, credentials=None, request=None, **kwargs):
    """Yanlış kullanıcı adı/şifre. (Yanlış doğrulama kodunu form kendisi sayar.)"""
    if request is not None:
        throttle.record_failure(throttle.request_ip(request))


@receiver(user_logged_in)
def on_login_ok(sender, request=None, **kwargs):
    if request is not None:
        throttle.clear(throttle.request_ip(request))
