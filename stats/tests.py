from unittest import mock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import DailyPage, DailyReferrer, DailyVisitor

UA = "Mozilla/5.0 (X11; Linux x86_64) Firefox/120.0"


class CountTests(TestCase):
    def setUp(self):
        self.c = Client(HTTP_HOST="localhost")

    def get(self, path="/", ua=UA, **extra):
        return self.c.get(path, HTTP_USER_AGENT=ua, **extra)

    def test_normal_page_counted_without_query(self):
        self.get("/?utm=x")
        row = DailyPage.objects.get()
        self.assertEqual((row.path, row.lang, row.views, row.unique), ("/", "tr", 1, 1))

    def test_english_lang(self):
        self.get("/en/")
        self.assertEqual(DailyPage.objects.get().lang, "en")

    def test_pjax_counted(self):
        self.get("/", HTTP_X_REQUESTED_WITH="pjax")
        self.assertEqual(DailyPage.objects.get().views, 1)

    def test_not_counted(self):
        self.get("/admin/login/")
        self.get("/static/nothing.css")
        self.get("/api/chat/")
        self.get("/sitemap.xml")
        self.get("/robots.txt")
        self.get("/yok-boyle-bir-sayfa/")
        for ua in ("Googlebot/2.1", "curl/8.0", "Lighthouse", "python-requests/2", "HeadlessChrome", ""):
            self.get("/", ua=ua)
        self.get("/", HTTP_DNT="1")
        self.get("/", HTTP_SEC_GPC="1")
        self.c.post("/", HTTP_USER_AGENT=UA)
        self.assertEqual(DailyPage.objects.count(), 0)
        self.assertEqual(DailyVisitor.objects.count(), 0)

    def test_same_visitor_one_unique(self):
        self.get("/")
        self.get("/")
        self.get("/en/")
        total = sum(DailyPage.objects.values_list("views", flat=True))
        unique = sum(DailyPage.objects.values_list("unique", flat=True))
        self.assertEqual((total, unique), (3, 1))
        self.assertEqual(DailyVisitor.objects.count(), 1)

    def test_different_visitors(self):
        self.get("/")
        self.get("/", ua="Mozilla/5.0 Safari/605")
        self.assertEqual(DailyPage.objects.get().unique, 2)

    def test_referrer_host_only_and_own_excluded(self):
        self.get("/", HTTP_REFERER="https://www.github.com/rosko35?tab=x")
        self.get("/", ua="Mozilla/5.0 Safari/1", HTTP_REFERER="https://localhost/blog/")
        self.get("/", ua="Mozilla/5.0 Safari/2", HTTP_REFERER="https://ozaydin.dev/")
        ref = DailyReferrer.objects.get()
        self.assertEqual((ref.host, ref.count), ("github.com", 1))

    def test_old_visitors_purged(self):
        from . import middleware
        from django.utils import timezone
        import datetime

        old = timezone.localdate() - datetime.timedelta(days=3)
        DailyVisitor.objects.create(date=old, hash="a" * 64)
        middleware._last_cleanup["date"] = None
        self.get("/")
        self.assertFalse(DailyVisitor.objects.filter(date=old).exists())

    def test_failure_does_not_break_page(self):
        with mock.patch("stats.middleware.record", side_effect=RuntimeError("boom")):
            with self.assertLogs("stats.middleware", level="ERROR"):
                response = self.get("/")
        self.assertEqual(response.status_code, 200)

    def test_query_count_small(self):
        self.get("/")  # ilk istek tabloları ısıtır
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            self.get("/", ua="Mozilla/5.0 Safari/9")
        ours = [q for q in ctx.captured_queries if "stats_" in q["sql"]]
        self.assertEqual(len(ours), 2)  # ziyaretçi INSERT + sayfa UPDATE


class AdminTests(TestCase):
    def setUp(self):
        self.url = reverse("admin:stats_summary")

    def test_anonymous_redirected(self):
        r = Client(HTTP_HOST="localhost").get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn("login", r["Location"])

    def test_staff_sees_summary(self):
        user = get_user_model().objects.create_superuser("a", "a@example.com", "pw")
        c = Client(HTTP_HOST="localhost")
        c.force_login(user)
        c.get("/", HTTP_USER_AGENT=UA)
        r = c.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "<svg")
        self.assertContains(r, "benzersiz ziyaretçi")
        self.assertEqual(c.get(reverse("admin:stats_dailypage_changelist")).status_code, 200)
