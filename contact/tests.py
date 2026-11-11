import smtplib
import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail, signing
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Message
from .views import TS_SALT, client_ip

TR_URL = "/iletisim/"
EN_URL = "/en/contact/"
FETCH = {"HTTP_X_REQUESTED_WITH": "fetch", "HTTP_ACCEPT": "application/json"}


def signed_ts(seconds_ago=60):
    """Geçmişte açılmış bir formun zaman damgası (imzanın kendi zamanı da geçmişe çekilir)."""
    past = time.time() - seconds_ago
    with mock.patch("time.time", return_value=past):
        return signing.TimestampSigner(salt=TS_SALT).sign(str(int(past)))


def payload(**kw):
    data = {
        "name": "Ayşe Yılmaz",
        "email": "ayse@example.com",
        "message": "Merhaba, projeleriniz hakkında konuşmak isterim.",
        "website": "",
        "ts": signed_ts(),
    }
    data.update(kw)
    return data


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CONTACT_TO="emre@example.com",
    SITE_URL="https://ozaydin.dev",
)
class ContactFormTests(TestCase):
    def setUp(self):
        self.c = Client(HTTP_HOST="localhost")

    def post(self, url=TR_URL, fetch=True, **kw):
        return self.c.post(url, payload(**kw), **(FETCH if fetch else {}))

    # --- sayfa ---
    def test_get_has_signed_ts(self):
        r = self.c.get(TR_URL)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["page_key"], "contact")
        ts = r.context["form_ts"]
        signing.TimestampSigner(salt=TS_SALT).unsign(ts, max_age=60)
        self.assertContains(r, f'value="{ts}"')

    # --- başarılı gönderim ---
    def test_success_json(self):
        r = self.post()
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        self.assertIn("Mesajın ulaştı", data["message"])
        msg = Message.objects.get()
        self.assertEqual((msg.name, msg.email, msg.lang), ("Ayşe Yılmaz", "ayse@example.com", "tr"))
        self.assertTrue(msg.emailed)
        self.assertFalse(msg.is_spam)
        self.assertEqual(msg.ip, "127.0.0.1")
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.subject, "ozaydin.dev · yeni mesaj: Ayşe Yılmaz")
        self.assertEqual(m.to, ["emre@example.com"])
        self.assertEqual(m.reply_to, ["ayse@example.com"])
        self.assertIn("https://ozaydin.dev" + reverse("admin:contact_message_change", args=[msg.pk]), m.body)
        self.assertIn("projeleriniz hakkında", m.body)

    def test_success_without_js_redirects(self):
        r = self.post(fetch=False)
        self.assertRedirects(r, TR_URL + "?gonderildi=1", fetch_redirect_response=False)
        self.assertEqual(Message.objects.count(), 1)
        r = self.c.get(TR_URL + "?gonderildi=1")
        self.assertContains(r, "Mesajın ulaştı")
        self.assertContains(r, 'class="note ok"')

    def test_en_success(self):
        r = self.post(EN_URL)
        self.assertEqual(r.json()["message"], "Your message arrived, thank you! I usually reply within a day.")
        self.assertEqual(Message.objects.get().lang, "en")

    def test_message_is_stripped(self):
        self.post(message="   " + "a" * 20 + "   ")
        self.assertEqual(Message.objects.get().body, "a" * 20)

    # --- doğrulama ---
    def test_validation_errors_json(self):
        r = self.post(name="  ", email="olmaz", message="kısa")
        self.assertEqual(r.status_code, 400)
        data = r.json()
        self.assertFalse(data["ok"])
        self.assertEqual(set(data["errors"]), {"name", "email", "message"})
        self.assertEqual(data["errors"]["email"], "Bu e-posta adresi geçerli görünmüyor.")
        self.assertEqual(data["errors"]["message"], "Mesaj en az 10 karakter olmalı.")
        self.assertFalse(Message.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_too_long_fields(self):
        r = self.post(name="x" * 101, message="y" * 5001)
        errors = r.json()["errors"]
        self.assertEqual(errors["name"], "Ad en fazla 100 karakter olabilir.")
        self.assertEqual(errors["message"], "Mesaj en fazla 5000 karakter olabilir.")

    def test_validation_errors_en(self):
        r = self.post(EN_URL, name="", email="nope", message="short")
        errors = r.json()["errors"]
        self.assertEqual(errors["name"], "Please enter your name.")
        self.assertEqual(errors["email"], "This email address doesn't look valid.")
        self.assertEqual(errors["message"], "Message must be at least 10 characters.")
        self.assertEqual(r.json()["message"], "Some fields need fixing.")

    def test_validation_errors_without_js_rerender(self):
        r = self.post(fetch=False, email="olmaz")
        self.assertEqual(r.status_code, 400)
        self.assertContains(r, 'class="field bad"', status_code=400)
        self.assertContains(r, '<p class="err" id="e-email">Bu e-posta adresi geçerli görünmüyor.</p>', status_code=400)
        self.assertContains(r, 'value="Ayşe Yılmaz"', status_code=400)
        self.assertContains(r, "projeleriniz hakkında", status_code=400)

    # --- spam ---
    def test_honeypot_silently_ok(self):
        r = self.post(website="http://spam.example")
        self.assertTrue(r.json()["ok"])
        self.assertFalse(Message.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_too_fast(self):
        r = self.post(ts=signed_ts(seconds_ago=1))
        self.assertTrue(r.json()["ok"])
        self.assertFalse(Message.objects.exists())

    def test_too_old(self):
        r = self.post(ts=signed_ts(seconds_ago=2 * 24 * 3600))
        self.assertTrue(r.json()["ok"])
        self.assertFalse(Message.objects.exists())

    def test_bad_signature(self):
        for ts in ("", "123", signed_ts() + "x", signing.TimestampSigner(salt="baska").sign("1")):
            r = self.post(ts=ts)
            self.assertTrue(r.json()["ok"])
        self.assertFalse(Message.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_rate_limit(self):
        for _ in range(5):
            self.assertEqual(self.post().status_code, 200)
        r = self.post()
        self.assertEqual(r.status_code, 429)
        self.assertEqual(r.json()["message"], "Çok fazla mesaj gönderdin, biraz sonra tekrar dene.")
        self.assertEqual(Message.objects.count(), 5)
        # Başka IP etkilenmez (Nginx arkasından gelen X-Forwarded-For)
        r = self.c.post(TR_URL, payload(), HTTP_X_FORWARDED_FOR="203.0.113.9", **FETCH)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Message.objects.first().ip, "203.0.113.9")

    def test_many_links_marked_spam(self):
        body = "Bakın: http://a.example https://b.example www.c.example http://d.example"
        r = self.post(message=body)
        self.assertTrue(r.json()["ok"])
        msg = Message.objects.get()
        self.assertTrue(msg.is_spam)
        self.assertFalse(msg.emailed)
        self.assertEqual(len(mail.outbox), 0)

    def test_three_links_ok(self):
        self.post(message="http://a.example https://b.example www.c.example")
        self.assertFalse(Message.objects.get().is_spam)
        self.assertEqual(len(mail.outbox), 1)

    # --- e-posta hatası ---
    def test_smtp_failure_keeps_message(self):
        with mock.patch("django.core.mail.EmailMessage.send", side_effect=smtplib.SMTPException("kapalı")):
            with self.assertLogs("contact.views", level="ERROR"):
                r = self.post()
        self.assertTrue(r.json()["ok"])
        msg = Message.objects.get()
        self.assertFalse(msg.emailed)

    def test_csrf_enforced(self):
        c = Client(HTTP_HOST="localhost", enforce_csrf_checks=True)
        r = c.post(TR_URL, payload(), **FETCH)
        self.assertEqual(r.status_code, 403)


class ClientIpTests(TestCase):
    def ip(self, remote, xff=None):
        from django.test import RequestFactory

        meta = {"REMOTE_ADDR": remote}
        if xff:
            meta["HTTP_X_FORWARDED_FOR"] = xff
        return client_ip(RequestFactory().get("/", **meta))

    def test_trusts_xff_only_behind_local_proxy(self):
        self.assertEqual(self.ip("127.0.0.1", "198.51.100.1, 10.0.0.1"), "198.51.100.1")
        self.assertEqual(self.ip("", "198.51.100.1"), "198.51.100.1")  # unix soket
        self.assertEqual(self.ip("198.51.100.7", "1.2.3.4"), "198.51.100.7")
        self.assertEqual(self.ip("127.0.0.1", "çöp"), None)


class AdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("emre", "e@example.com", "x")
        self.c = Client(HTTP_HOST="localhost")
        self.c.force_login(self.user)
        self.m1 = Message.objects.create(name="A", email="a@example.com", body="Merhaba dünya, nasılsın?")
        self.m2 = Message.objects.create(name="B", email="b@example.com", body="İkinci mesaj burada.")

    def test_changelist_shows_unread_and_reply(self):
        r = self.c.get(reverse("admin:contact_message_changelist"))
        self.assertContains(r, "2 okunmamış")
        self.assertContains(r, "mailto:a@example.com?subject=Re%3A%20ozaydin.dev")

    def test_open_marks_read(self):
        self.c.get(reverse("admin:contact_message_change", args=[self.m1.pk]))
        self.m1.refresh_from_db()
        self.assertTrue(self.m1.is_read)

    def test_actions(self):
        url = reverse("admin:contact_message_changelist")
        self.c.post(url, {"action": "mark_spam", "_selected_action": [self.m2.pk]})
        self.m2.refresh_from_db()
        self.assertTrue(self.m2.is_spam)
        self.c.post(url, {"action": "mark_read", "_selected_action": [self.m1.pk]})
        self.m1.refresh_from_db()
        self.assertTrue(self.m1.is_read)
