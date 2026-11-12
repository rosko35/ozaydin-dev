from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice


class Command(BaseCommand):
    help = "Kullanıcının doğrulama cihazlarını ve yedek kodlarını siler (telefon ve yedek kodlar kaybolduysa)."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, username, **options):
        try:
            user = get_user_model().objects.get(**{get_user_model().USERNAME_FIELD: username})
        except get_user_model().DoesNotExist:
            raise CommandError(f"Kullanıcı bulunamadı: {username}")
        totp, _ = TOTPDevice.objects.filter(user=user).delete()
        static, _ = StaticDevice.objects.filter(user=user).delete()
        self.stdout.write(f"{username}: {totp} cihaz ve {static} yedek kod cihazı silindi.")
        self.stdout.write("Giriş yapabilmek için sunucuda DJANGO_ADMIN_2FA=0 olmalı; girince cihazı yeniden kur.")
