from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
import tempfile

from .models import Project


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProjectPageTests(TestCase):
    def test_list_and_detail_both_languages(self):
        for url in ("/projeler/", "/projeler/safe-city-2072/", "/en/projects/", "/en/projects/safe-city-2072/"):
            self.assertEqual(self.client.get(url, HTTP_HOST="localhost").status_code, 200, url)

    def test_demo_video_shown_when_uploaded(self):
        p = Project.objects.get(slug="safe-city-2072")
        r = self.client.get("/projeler/safe-city-2072/", HTTP_HOST="localhost")
        self.assertNotContains(r, "<video")
        p.video.save("demo.mp4", ContentFile(b"\x00\x00\x00\x18ftypmp42"), save=True)
        r = self.client.get("/projeler/safe-city-2072/", HTTP_HOST="localhost")
        self.assertContains(r, "<video")
        self.assertContains(r, 'type="video/mp4"')

    def test_index_row_image_only_with_cover(self):
        # Proje dizininde imleci izleyen kart: kapağı olan projede görsel var, olmayanda yok.
        from io import BytesIO
        from PIL import Image
        r = self.client.get("/", HTTP_HOST="localhost")
        self.assertNotContains(r, "data-peek=")
        buf = BytesIO()
        Image.new("RGB", (64, 48), "gray").save(buf, "PNG")
        p = Project.objects.get(slug="safe-city-2072")
        p.cover.save("k.png", ContentFile(buf.getvalue()), save=True)
        for url in ("/", "/projeler/", "/en/projects/"):
            r = self.client.get(url, HTTP_HOST="localhost")
            self.assertContains(r, "data-peek=", count=1)
            self.assertContains(r, 'class="shot"')

    def test_card_uses_small_webp_copy(self):
        # Kart tam boy kapağı değil, 640 px genişliğinde WebP kopyayı yükler; kapak değişince kopya yenilenir.
        from io import BytesIO
        from django.core.management import call_command
        from PIL import Image

        def png(w, h, color):
            buf = BytesIO()
            Image.new("RGB", (w, h), color).save(buf, "PNG")
            return ContentFile(buf.getvalue())

        p = Project.objects.get(slug="safe-city-2072")
        p.cover.save("buyuk.png", png(1600, 1200, "gray"), save=True)
        updated = Project.objects.get(pk=p.pk).updated
        r = self.client.get("/projeler/", HTTP_HOST="localhost")
        p.refresh_from_db()
        self.assertTrue(p.card_thumb.name.startswith("projects/cards/"))
        self.assertTrue(p.card_thumb.name.endswith(".webp"))
        self.assertEqual((p.card_w, p.card_h), (640, 480))
        self.assertEqual(p.updated, updated)
        self.assertContains(r, f'data-peek="{p.card_thumb.url}"')
        # Projeler sayfasında ilk satır hemen yüklenir; ana sayfada (aşağıda kalır) geç yüklenir.
        self.assertContains(r, f'<img src="{p.card_thumb.url}" alt="" width="640" height="480" decoding="async"')
        self.assertNotContains(r, p.cover.url)
        r = self.client.get("/", HTTP_HOST="localhost")
        self.assertContains(r, f'<img src="{p.card_thumb.url}" alt="" width="640" height="480" loading="lazy"')

        first = p.card_thumb.name
        p.cover.save("yeni.png", png(800, 800, "red"), save=True)
        call_command("kart_gorselleri", stdout=__import__("io").StringIO())
        p.refresh_from_db()
        self.assertNotEqual(p.card_thumb.name, first)
        self.assertEqual((p.card_w, p.card_h), (640, 640))
        self.assertFalse(p.card_thumb.storage.exists(first))


NEW_PROJECTS = {
    3: "mini-siem", 4: "ssh-honeypot", 5: "async-vuln-scanner", 6: "net-traffic-analyzer",
    7: "server-hardening", 8: "iot-sensor-panel", 9: "homelab-security-panel",
}


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class NewProjectsTests(TestCase):
    def test_seven_new_projects_with_fixed_numbers(self):
        qs = Project.objects.filter(slug__in=NEW_PROJECTS.values())
        self.assertEqual(qs.count(), 7)
        self.assertEqual(dict(qs.values_list("number", "slug")), NEW_PROJECTS)

    def test_both_summaries_and_categories_filled(self):
        for p in Project.objects.filter(slug__in=NEW_PROJECTS.values()):
            self.assertTrue(p.summary_tr.strip(), p.slug)
            self.assertTrue(p.summary_en.strip(), p.slug)
            self.assertIn(p.categories.count(), (1, 2), p.slug)
            self.assertEqual(p.repo_url, f"https://github.com/rosko35/{p.slug}")

    def test_featured_only_selected(self):
        featured = set(Project.objects.filter(slug__in=NEW_PROJECTS.values(), featured=True).values_list("slug", flat=True))
        self.assertEqual(featured, {"mini-siem", "ssh-honeypot", "server-hardening", "homelab-security-panel"})

    def test_detail_pages_both_languages(self):
        for slug in NEW_PROJECTS.values():
            for url in (f"/projeler/{slug}/", f"/en/projects/{slug}/"):
                self.assertEqual(self.client.get(url, HTTP_HOST="localhost").status_code, 200, url)
