import base64
import re

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django_otp.oath import totp as oath_totp
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

from django.conf import settings

from .models import LoginAttempt

PASSWORD = "dogru-sifre-12345"
LOGIN_URL = "/" + settings.ADMIN_URL + "login/"
INDEX_URL = "/" + settings.ADMIN_URL
SETUP_URL = "/" + settings.ADMIN_URL + "2fa/"


def make_client():
    return Client(HTTP_HOST="localhost", REMOTE_ADDR="127.0.0.1")


def current_code(device):
    return "%06d" % oath_totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits)


class Base(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.enterClassContext(
            override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])  # testler hızlı olsun
        )

    def setUp(self):
        self.user = get_user_model().objects.create_superuser("emre", "e@example.com", PASSWORD)
        self.client = make_client()

    def login(self, token=None, password=PASSWORD, client=None):
        data = {"username": "emre", "password": password, "next": INDEX_URL}
        if token is not None:
            data["otp_token"] = token
        return (client or self.client).post(LOGIN_URL, data)

    def make_device(self):
        return TOTPDevice.objects.create(user=self.user, name="t", confirmed=True)

    def admin_ok(self, client=None):
        return (client or self.client).get(INDEX_URL).status_code == 200


@override_settings(ADMIN_2FA=False)
class NotEnforcedTests(Base):
    def test_normal_login_without_code(self):
        r = self.login()
        self.assertRedirects(r, INDEX_URL, fetch_redirect_response=False)
        self.assertTrue(self.admin_ok())

    def test_existing_admin_registrations_still_work(self):
        self.login()
        for url in ("auth/user/", "blog/", "projects/"):
            self.assertIn(self.client.get(INDEX_URL + url).status_code, (200, 302, 404))
        self.assertEqual(self.client.get(INDEX_URL + "auth/user/").status_code, 200)

    def test_index_warns_when_no_device(self):
        self.login()
        r = self.client.get(INDEX_URL)
        self.assertContains(r, "İki adımlı doğrulama kurulmamış")
        self.assertContains(r, SETUP_URL)

    def test_index_notes_when_device_but_not_enforced(self):
        self.make_device()
        self.login()
        self.assertContains(self.client.get(INDEX_URL), "henüz zorunlu değil")

    def test_setup_requires_login(self):
        r = self.client.get(SETUP_URL)
        self.assertEqual(r.status_code, 302)
        self.assertIn("login", r["Location"])

    def test_setup_forbidden_for_non_superuser(self):
        get_user_model().objects.create_user("staff", "s@example.com", PASSWORD, is_staff=True)
        c = make_client()
        c.post(LOGIN_URL, {"username": "staff", "password": PASSWORD})
        self.assertEqual(c.get(SETUP_URL).status_code, 403)

    def test_setup_shows_qr_and_secret_and_confirms(self):
        self.login()
        r = self.client.get(SETUP_URL)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "data:image/svg+xml;base64,")
        device = TOTPDevice.objects.get(user=self.user)
        self.assertFalse(device.confirmed)
        secret = base64.b32encode(device.bin_key).decode()
        self.assertContains(r, secret)
        # QR gerçekten svg mi
        b64 = re.search(r"data:image/svg\+xml;base64,([^\"]+)", r.content.decode()).group(1)
        self.assertIn(b"<svg", base64.b64decode(b64))
        # Yenileyince aynı anahtar (yeni cihaz üretilmez)
        r2 = self.client.get(SETUP_URL)
        self.assertContains(r2, secret)
        self.assertEqual(TOTPDevice.objects.filter(user=self.user).count(), 1)

        # Yanlış kod
        r = self.client.post(SETUP_URL, {"action": "confirm", "token": "000000"})
        self.assertContains(r, "Kod hatalı")
        device.refresh_from_db()
        self.assertFalse(device.confirmed)

        # Doğru kod: onaylanır, 10 yedek kod gösterilir (yanlış denemenin cihaz beklemesini sıfırla)
        device.refresh_from_db()
        device.throttle_reset()
        r = self.client.post(SETUP_URL, {"action": "confirm", "token": current_code(device)})
        self.assertContains(r, "Yedek kodlar")
        device.refresh_from_db()
        self.assertTrue(device.confirmed)
        codes = re.findall(r"<li>([a-z2-7]{4}-[a-z2-7]{4})</li>", r.content.decode())
        self.assertEqual(len(codes), 10)
        self.assertEqual(StaticDevice.objects.get(user=self.user).token_set.count(), 10)
        # Kodlar yeniden yüklemede bir daha gösterilmez
        r = self.client.get(SETUP_URL)
        self.assertNotContains(r, codes[0])
        self.assertContains(r, "Cihaz kurulu")

    def test_regenerate_backup_codes_needs_password(self):
        self.login()
        self.make_device()
        r = self.client.post(SETUP_URL, {"action": "new_codes", "password": "yanlis"}, follow=True)
        self.assertContains(r, "Şifre yanlış")
        r = self.client.post(SETUP_URL, {"action": "new_codes", "password": PASSWORD})
        self.assertEqual(len(re.findall(r"<li>[a-z2-7]{4}-[a-z2-7]{4}</li>", r.content.decode())), 10)

    def test_reset_device_needs_password(self):
        self.login()
        self.make_device()
        self.client.post(SETUP_URL, {"action": "reset", "password": "yanlis"})
        self.assertTrue(TOTPDevice.objects.filter(user=self.user, confirmed=True).exists())
        self.client.post(SETUP_URL, {"action": "reset", "password": PASSWORD})
        self.assertFalse(TOTPDevice.objects.filter(user=self.user, confirmed=True).exists())


@override_settings(ADMIN_2FA=True)
class EnforcedTests(Base):
    def test_login_form_shows_code_field(self):
        self.assertContains(self.client.get(LOGIN_URL), 'name="otp_token"')

    def test_no_device_user_cannot_enter(self):
        self.assertEqual(self.login().status_code, 200)  # kod yok: form tekrar
        self.assertFalse(self.admin_ok())
        self.assertEqual(self.login(token="123456").status_code, 200)
        self.assertFalse(self.admin_ok())

    def test_device_user_without_code_cannot_enter(self):
        self.make_device()
        r = self.login()
        self.assertContains(r, "Doğrulama kodunu da gir")
        self.assertFalse(self.admin_ok())

    def test_correct_code_enters(self):
        device = self.make_device()
        r = self.login(token=current_code(device))
        self.assertRedirects(r, INDEX_URL, fetch_redirect_response=False)
        self.assertTrue(self.admin_ok())

    def test_wrong_code_does_not_enter(self):
        self.make_device()
        r = self.login(token="000000")
        self.assertContains(r, "Doğrulama kodu hatalı")
        self.assertFalse(self.admin_ok())

    def test_wrong_password_with_right_code_does_not_enter(self):
        device = self.make_device()
        self.login(token=current_code(device), password="yanlis")
        self.assertFalse(self.admin_ok())

    def test_replayed_code_rejected(self):
        device = self.make_device()
        code = current_code(device)
        self.login(token=code)
        c2 = make_client()
        self.login(token=code, client=c2)
        self.assertFalse(self.admin_ok(c2))

    def test_backup_code_is_single_use(self):
        self.make_device()
        static = StaticDevice.objects.create(user=self.user, name="y", confirmed=True)
        from django_otp.plugins.otp_static.models import StaticToken

        StaticToken.objects.create(device=static, token="abcdefgh")
        StaticToken.objects.create(device=static, token="klmnpqrs")

        r = self.login(token="abcd-efgh")
        self.assertRedirects(r, INDEX_URL, fetch_redirect_response=False)
        self.assertTrue(self.admin_ok())

        c2 = make_client()
        r = self.login(token="abcdefgh", client=c2)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(self.admin_ok(c2))

    def test_session_without_verification_is_kicked_from_admin(self):
        # Zorunluluk açılmadan önce şifreyle girmiş bir oturum, doğrulanmadığı için admin'e giremez.
        with override_settings(ADMIN_2FA=False):
            self.login()
            self.assertTrue(self.admin_ok())
        self.make_device()
        r = self.client.get(INDEX_URL)
        self.assertEqual(r.status_code, 302)
        self.assertIn("login", r["Location"])

    def test_setup_page_needs_verified_session(self):
        r = self.client.get(SETUP_URL)
        self.assertEqual(r.status_code, 302)

    def test_verified_session_can_see_status_but_not_reset(self):
        device = self.make_device()
        self.login(token=current_code(device))
        self.assertContains(self.client.get(SETUP_URL), "Cihaz kurulu")
        self.client.post(SETUP_URL, {"action": "reset", "password": PASSWORD})
        self.assertTrue(TOTPDevice.objects.filter(user=self.user, confirmed=True).exists())

    def test_reset_2fa_command(self):
        self.make_device()
        StaticDevice.objects.create(user=self.user, name="y", confirmed=True)
        call_command("reset_2fa", "emre", stdout=open("/dev/null", "w"))
        self.assertFalse(TOTPDevice.objects.exists())
        self.assertFalse(StaticDevice.objects.exists())


@override_settings(ADMIN_2FA=False)
class ThrottleTests(Base):
    def test_sixth_attempt_blocked_even_with_right_password(self):
        for _ in range(5):
            r = self.login(password="yanlis")
            self.assertEqual(r.status_code, 200)
            self.assertNotContains(r, "Çok fazla deneme")
        r = self.login()  # doğru şifre
        self.assertEqual(r.status_code, 429)
        self.assertContains(r, "Çok fazla deneme, 15 dakika sonra tekrar dene.", status_code=429)
        self.assertFalse(self.admin_ok())
        self.assertEqual(LoginAttempt.objects.count(), 5)  # engelliyken sayılmaz

    def test_block_is_per_ip(self):
        for _ in range(5):
            self.login(password="yanlis")
        other = Client(HTTP_HOST="localhost", REMOTE_ADDR="10.9.9.9")
        r = self.login(client=other)
        self.assertEqual(r.status_code, 302)

    def test_block_expires(self):
        from datetime import timedelta
        from django.utils import timezone

        for _ in range(5):
            self.login(password="yanlis")
        LoginAttempt.objects.update(blocked_until=None)  # engel süresi doldu
        LoginAttempt.objects.update(created_at=timezone.now() - timedelta(minutes=16))
        r = self.login()
        self.assertEqual(r.status_code, 302)

    def test_old_failures_do_not_count(self):
        from datetime import timedelta
        from django.utils import timezone

        for _ in range(4):
            self.login(password="yanlis")
        LoginAttempt.objects.update(created_at=timezone.now() - timedelta(minutes=16))
        self.login(password="yanlis")  # pencerede 1 tane
        self.assertEqual(self.login().status_code, 302)

    def test_success_clears_counter(self):
        for _ in range(3):
            self.login(password="yanlis")
        self.login()
        self.assertEqual(LoginAttempt.objects.count(), 0)

    @override_settings(ADMIN_2FA=True)
    def test_wrong_codes_count_too(self):
        self.make_device()
        for _ in range(5):
            self.login(token="000000")
        device = TOTPDevice.objects.get()
        r = self.login(token=current_code(device))  # doğru kod bile geçmez
        self.assertEqual(r.status_code, 429)
        self.assertFalse(self.admin_ok())

    def test_forwarded_ip_used_behind_proxy(self):
        # client_ip: yerel adresten gelen istekte X-Forwarded-For'a güvenilir; farklı ziyaretçiler ayrı sayılır.
        for _ in range(5):
            self.client.post(LOGIN_URL, {"username": "emre", "password": "x"}, HTTP_X_FORWARDED_FOR="203.0.113.5")
        self.assertEqual(LoginAttempt.objects.filter(ip="203.0.113.5").count(), 5)
        r = self.client.post(LOGIN_URL, {"username": "emre", "password": PASSWORD}, HTTP_X_FORWARDED_FOR="198.51.100.7")
        self.assertEqual(r.status_code, 302)
