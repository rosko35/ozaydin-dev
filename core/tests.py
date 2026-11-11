import json
import re
import shutil
import tempfile
from io import BytesIO

from django.test import Client, TestCase, override_settings
from PIL import Image

from core import seo
from projects.models import Project

TMP_MEDIA = tempfile.mkdtemp(prefix="ozaydin-test-media-")

PAGES = [
    "/", "/en/", "/projeler/", "/en/projects/", "/blog/", "/en/blog/",
    "/hakkimda/", "/en/about/", "/iletisim/", "/en/contact/",
    "/projeler/safe-city-2072/", "/en/projects/safe-city-2072/",
]


def jsonld_blocks(html):
    return [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]


@override_settings(MEDIA_ROOT=TMP_MEDIA, SITE_URL="https://ozaydin.dev")
class SeoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.c = Client(HTTP_HOST="localhost")

    def test_head_on_every_page(self):
        for url in PAGES:
            with self.subTest(url=url):
                r = self.c.get(url)
                self.assertEqual(r.status_code, 200)
                html = r.content.decode()
                self.assertIn(f'<link rel="canonical" href="https://ozaydin.dev{url}">', html)
                for lang in ("tr", "en", "x-default"):
                    self.assertIn(f'hreflang="{lang}" href="https://ozaydin.dev/', html)
                self.assertRegex(html, r'<meta property="og:image" content="https://ozaydin\.dev/og/[^"]+\.png')
                self.assertIn('<meta property="og:image:width" content="1200">', html)
                self.assertIn('<meta name="twitter:card" content="summary_large_image">', html)
                self.assertIn('<meta property="og:locale" content="{}">'.format(
                    "en_US" if url.startswith("/en/") else "tr_TR"), html)
                self.assertNotIn('name="robots"', html)
                self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1, "her sayfada tek h1")
                blocks = jsonld_blocks(html)
                self.assertEqual(len(blocks), 1)
                types = {n["@type"] for n in blocks[0]["@graph"]}
                self.assertTrue({"WebSite", "Person"} <= types)

    def test_project_jsonld(self):
        html = self.c.get("/en/projects/safe-city-2072/").content.decode()
        graph = jsonld_blocks(html)[0]["@graph"]
        work = next(n for n in graph if n["@type"] == "CreativeWork")
        self.assertEqual(work["name"], "Safe City: 2072")
        self.assertEqual(work["url"], "https://ozaydin.dev/en/projects/safe-city-2072/")
        self.assertEqual(work["dateCreated"], "2026")
        self.assertIn("/og/project/safe-city-2072-en.png?v=", work["image"])
        crumbs = next(n for n in graph if n["@type"] == "BreadcrumbList")
        self.assertEqual(len(crumbs["itemListElement"]), 3)
        self.assertIn('<meta property="og:type" content="website">', html)

    def test_jsonld_escapes_script_end(self):
        out = seo.jsonld({"x": "</script><b>&"})
        self.assertNotIn("<", out)
        self.assertEqual(json.loads(out)["x"], "</script><b>&")

    def test_canonical_drops_query_keeps_page(self):
        html = self.c.get("/projeler/?utm_source=x").content.decode()
        self.assertIn('<link rel="canonical" href="https://ozaydin.dev/projeler/">', html)
        html = self.c.get("/blog/?page=2&utm=x").content.decode()
        self.assertIn('<link rel="canonical" href="https://ozaydin.dev/blog/?page=2">', html)

    def test_404_noindex(self):
        r = self.c.get("/yok-boyle-bir-sayfa/")
        self.assertEqual(r.status_code, 404)
        html = r.content.decode()
        self.assertIn('<meta name="robots" content="noindex">', html)
        self.assertNotIn('rel="canonical"', html)

    def test_noindex_context(self):
        from django.template import Context, Template
        from django.test import RequestFactory

        req = RequestFactory().get("/", HTTP_HOST="localhost")
        html = Template('{% include "core/_meta.html" %}').render(Context({"request": req, "noindex": True}))
        self.assertIn('<meta name="robots" content="noindex">', html)

    def test_article_meta(self):
        """Blog modeli olmadan: yazı görünümünün context'e koyacağı `article` yerine benzer bir nesne."""
        from datetime import datetime, timezone
        from types import SimpleNamespace

        from django.template import Context, Template
        from django.test import RequestFactory
        from django.urls import resolve

        req = RequestFactory().get("/blog/ilk-yazi/", HTTP_HOST="localhost")
        req.resolver_match = resolve("/blog/ilk-yazi/")
        art = SimpleNamespace(
            title_tr="İlk yazı </script>", title_en="", summary_tr="Özet", slug="ilk-yazi",
            published_at=datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc),
            updated=datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc),
        )
        ctx = {"request": req, "article": art, "page_title": art.title_tr, "page_description": "Özet",
               "og_image": "https://ozaydin.dev/media/kapak.webp"}
        html = Template('{% include "core/_meta.html" %}').render(Context(ctx))
        self.assertIn('<meta property="og:type" content="article">', html)
        self.assertIn('<meta property="article:published_time" content="2026-11-01T09:00:00+00:00">', html)
        self.assertIn('<meta property="article:modified_time" content="2026-11-02T09:00:00+00:00">', html)
        self.assertIn('content="https://ozaydin.dev/og/post/ilk-yazi-tr.png?v=', html)
        graph = jsonld_blocks(html)[0]["@graph"]
        post = next(n for n in graph if n["@type"] == "BlogPosting")
        self.assertEqual(post["headline"], "İlk yazı </script>")
        self.assertEqual(post["datePublished"], "2026-11-01T09:00:00+00:00")
        self.assertEqual(post["mainEntityOfPage"]["@id"], "https://ozaydin.dev/blog/ilk-yazi/")
        self.assertTrue(any(n["@type"] == "BreadcrumbList" for n in graph))

    def test_sitemap(self):
        r = self.c.get("/sitemap.xml")
        self.assertEqual(r.status_code, 200)
        xml = r.content.decode()
        self.assertIn("<loc>https://ozaydin.dev/</loc>", xml)
        self.assertIn("<loc>https://ozaydin.dev/en/</loc>", xml)
        self.assertIn("<loc>https://ozaydin.dev/projeler/safe-city-2072/</loc>", xml)
        self.assertIn("<loc>https://ozaydin.dev/en/projects/safe-city-2072/</loc>", xml)
        self.assertIn('hreflang="en" href="https://ozaydin.dev/en/about/"', xml)
        self.assertIn('hreflang="tr" href="https://ozaydin.dev/hakkimda/"', xml)
        self.assertIn('hreflang="x-default" href="https://ozaydin.dev/hakkimda/"', xml)
        self.assertIn("<lastmod>", xml)
        self.assertNotIn("localhost", xml)

    def test_robots(self):
        r = self.c.get("/robots.txt")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r["Content-Type"].startswith("text/plain"))
        body = r.content.decode()
        self.assertIn("User-agent: *", body)
        self.assertIn("Sitemap: https://ozaydin.dev/sitemap.xml", body)
        self.assertNotIn("/og/", body)

    def _png(self, url):
        r = self.c.get(url)
        self.assertEqual(r.status_code, 200, url)
        self.assertEqual(r["Content-Type"], "image/png")
        self.assertIn("max-age=86400", r["Cache-Control"])
        img = Image.open(BytesIO(b"".join(r.streaming_content) if r.streaming else r.content))
        self.assertEqual(img.size, (1200, 630))

    def test_og_images(self):
        for url in ["/og/home-tr.png", "/og/home-en.png", "/og/page/projects-tr.png", "/og/page/contact-en.png",
                    "/og/project/safe-city-2072-tr.png", "/og/project/ozaydin-dev-en.png"]:
            with self.subTest(url=url):
                self._png(url)
        # ikinci istek diskten
        self._png("/og/project/safe-city-2072-tr.png")
        self.assertEqual(self.c.get("/og/project/yok-tr.png").status_code, 404)
        self.assertEqual(self.c.get("/og/page/admin-tr.png").status_code, 404)
        self.assertEqual(self.c.get("/og/post/yok-tr.png").status_code, 404)

    def test_og_cache_renews_on_title_change(self):
        from pathlib import Path

        self._png("/og/project/ozaydin-dev-tr.png")
        folder = Path(TMP_MEDIA) / "og"
        before = set(folder.glob("project-ozaydin-dev-tr-*.png"))
        p = Project.objects.get(slug="ozaydin-dev")
        p.title = "ozaydin.dev v2"
        p.save()
        self._png("/og/project/ozaydin-dev-tr.png")
        after = set(folder.glob("project-ozaydin-dev-tr-*.png"))
        self.assertEqual(len(after), 1)
        self.assertNotEqual(before, after)

    def test_icons_and_manifest(self):
        r = self.c.get("/favicon.ico")
        self.assertEqual(r.status_code, 302)
        self.assertIn("core/icons/favicon", r["Location"])
        r = self.c.get("/site.webmanifest")
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)
        self.assertEqual(data["short_name"], "ozaydin.dev")
        self.assertEqual({i["sizes"] for i in data["icons"]}, {"192x192", "512x512"})
        html = self.c.get("/").content.decode()
        self.assertIn('rel="apple-touch-icon"', html)
        self.assertIn('rel="manifest"', html)
