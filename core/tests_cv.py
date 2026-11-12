import re

from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.test import Client, TestCase


class CvTests(TestCase):
    def get(self, path):
        return Client(HTTP_HOST="localhost").get(path).content.decode()

    def test_static_files_exist(self):
        for code in ("EN", "TR"):
            self.assertTrue(finders.find(f"core/cv/Emre_Ozaydin_CV_{code}.pdf"))

    def test_about_links(self):
        for path, main, other in (("/hakkimda/", "TR", "EN"), ("/en/about/", "EN", "TR")):
            html = self.get(path)
            self.assertIn(static(f"core/cv/Emre_Ozaydin_CV_{other}.pdf"), html)
            first = re.search(r'class="btn solid" href="([^"]+\.pdf)"', html)
            self.assertIsNotNone(first)
            self.assertEqual(first.group(1), static(f"core/cv/Emre_Ozaydin_CV_{main}.pdf"))
            self.assertIn("data-no-pjax", html)

    def test_contact_link(self):
        self.assertIn("CV_TR", self.get("/iletisim/"))
        self.assertIn("CV_EN", self.get("/en/contact/"))
