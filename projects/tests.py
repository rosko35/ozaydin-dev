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
