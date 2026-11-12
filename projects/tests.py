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
