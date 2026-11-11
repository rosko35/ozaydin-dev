import shutil
import tempfile
from datetime import timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.utils import timezone, translation
from PIL import Image

from projects.models import Project

from .markdown import clean, render
from .models import Post, PostImage, Tag
from .selectors import latest_posts


def make_post(slug="yazi", status=Post.Status.PUBLISHED, **kw):
    data = {
        "title_tr": f"Başlık {slug}", "title_en": f"Title {slug}", "slug": slug,
        "summary_tr": "Türkçe özet", "summary_en": "English summary",
        "body_tr": "Türkçe **gövde** metni.", "body_en": "English **body** text.",
        "status": status,
    }
    data.update(kw)
    return Post.objects.create(**data)


class Base(TestCase):
    def setUp(self):
        self.c = Client(HTTP_HOST="localhost")
        # Data migration'daki taslak yazı testleri etkilemesin
        Post.objects.all().delete()


class VisibilityTests(Base):
    def test_published_manager(self):
        pub = make_post("pub")
        make_post("draft", status=Post.Status.DRAFT)
        make_post("future", published_at=timezone.now() + timedelta(days=2))
        self.assertEqual(list(Post.objects.published()), [pub])

    def test_published_at_set_on_publish(self):
        p = make_post("x")
        self.assertIsNotNone(p.published_at)
        d = make_post("d", status=Post.Status.DRAFT)
        self.assertIsNone(d.published_at)

    def test_draft_404_and_preview(self):
        make_post("taslak", status=Post.Status.DRAFT)
        self.assertEqual(self.c.get("/blog/taslak/").status_code, 404)
        self.assertEqual(self.c.get("/blog/taslak/?onizleme=1").status_code, 404)
        get_user_model().objects.create_superuser("emre", "e@example.com", "x")
        self.c.login(username="emre", password="x")
        self.assertEqual(self.c.get("/blog/taslak/").status_code, 404)
        r = self.c.get("/blog/taslak/?onizleme=1")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Taslak önizleme")
        self.assertContains(r, 'name="robots" content="noindex"')

    def test_draft_not_in_list_or_home(self):
        make_post("gorunur")
        make_post("gizli", status=Post.Status.DRAFT)
        r = self.c.get("/blog/")
        self.assertContains(r, "/blog/gorunur/")
        self.assertNotContains(r, "/blog/gizli/")
        self.assertEqual([p.slug for p in latest_posts(3)], ["gorunur"])
        self.assertContains(self.c.get("/"), "/blog/gorunur/")


class PageTests(Base):
    def test_list_tr_en(self):
        make_post("a")
        r = self.c.get("/blog/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["page_key"], "blog")
        self.assertContains(r, "Başlık a")
        self.assertContains(r, "1 yazı")
        r = self.c.get("/en/blog/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Title a")
        self.assertContains(r, "/en/blog/a/")

    def test_empty_list(self):
        r = self.c.get("/blog/")
        self.assertContains(r, "Henüz yazı yok")

    def test_pagination(self):
        for i in range(12):
            make_post(f"p{i}", published_at=timezone.now() - timedelta(days=i))
        r = self.c.get("/blog/")
        self.assertEqual(len(r.context["posts"]), 10)
        self.assertContains(r, "?page=2")
        r = self.c.get("/blog/?page=2")
        self.assertEqual(len(r.context["posts"]), 2)
        self.assertEqual(self.c.get("/blog/?page=99").status_code, 200)

    def test_detail_tr_en(self):
        project = Project.objects.get(slug="ozaydin-dev")
        older = make_post("eski", published_at=timezone.now() - timedelta(days=3))
        p = make_post("yeni", related_project=project, body_tr="## Ağ ayarları\n\nMetin.")
        r = self.c.get("/blog/yeni/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["page_key"], "post")
        self.assertEqual(r.context["article"], p)
        self.assertIsNone(r.context["og_image"])
        self.assertEqual(r.context["page_description"], "Türkçe özet")
        self.assertContains(r, 'id="ag-ayarlari"')
        self.assertContains(r, "İlgili proje")
        self.assertContains(r, "/projeler/ozaydin-dev/")
        self.assertContains(r, 'data-form="d-10"')  # 2. yazı
        self.assertEqual(r.context["prev_post"], older)
        r = self.c.get("/en/blog/yeni/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Title yeni")
        self.assertContains(r, "English <strong>body</strong> text.")
        self.assertEqual(r.context["page_description"], "English summary")

    def test_en_falls_back_to_tr(self):
        make_post("sadece-tr", title_en="", summary_en="", body_en="")
        r = self.c.get("/en/blog/")
        self.assertContains(r, "Başlık sadece-tr")
        self.assertContains(r, "only in Turkish")
        r = self.c.get("/en/blog/sadece-tr/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Türkçe <strong>gövde</strong> metni.")
        self.assertContains(r, "This post is only in Turkish for now.")
        self.assertContains(r, 'class="prose" lang="tr"')
        # Türkçe sayfada not çıkmaz
        self.assertNotContains(self.c.get("/blog/sadece-tr/"), "sadece Türkçe")

    def test_tag_page(self):
        t = Tag.objects.create(name_tr="sunucu", name_en="server", slug="sunucu-test")
        p = make_post("etiketli")
        p.tags.add(t)
        make_post("etiketsiz")
        r = self.c.get("/blog/etiket/sunucu-test/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "#sunucu")
        self.assertContains(r, "/blog/etiketli/")
        self.assertNotContains(r, "/blog/etiketsiz/")
        r = self.c.get("/en/blog/tag/sunucu-test/")
        self.assertContains(r, "#server")
        self.assertEqual(self.c.get("/blog/etiket/yok/").status_code, 404)


class FeedTests(Base):
    def test_rss_tr_en(self):
        make_post("rss-yazi")
        make_post("taslak-rss", status=Post.Status.DRAFT)
        r = self.c.get("/blog/rss/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r["Content-Type"].startswith("application/rss+xml"))
        body = r.content.decode()
        self.assertIn("<language>tr</language>", body)
        self.assertIn("<link>http://localhost/blog/</link>", body)
        self.assertIn("<link>http://localhost/blog/rss-yazi/</link>", body)
        self.assertIn("Başlık rss-yazi", body)
        self.assertIn("Türkçe özet", body)
        self.assertNotIn("taslak-rss", body)
        r = self.c.get("/en/blog/rss/")
        body = r.content.decode()
        self.assertIn("<language>en</language>", body)
        self.assertIn("Title rss-yazi", body)
        self.assertIn("English summary", body)
        self.assertIn("<link>http://localhost/en/blog/rss-yazi/</link>", body)

    def test_reserved_slug(self):
        from django.core.exceptions import ValidationError
        p = Post(title_tr="x", slug="rss", summary_tr="x", body_tr="x")
        with self.assertRaises(ValidationError):
            p.full_clean()


class MarkdownTests(TestCase):
    def test_script_and_js_links_removed(self):
        html = render(
            "Merhaba <script>alert(1)</script>\n\n"
            "[tıkla](javascript:alert(1)) [b](JaVa\tScRipt:alert(2))\n\n"
            '<a href="&#106;avascript:alert(3)">x</a> <img src="x.png" onerror="alert(4)">\n\n'
            '<iframe src="https://evil.example"></iframe><div onclick="x()">d</div>'
        )
        self.assertNotIn("<script", html)
        self.assertNotIn("alert(1)", html)
        self.assertNotIn("javascript", html.lower())
        self.assertNotIn("onerror", html)
        self.assertNotIn("onclick", html)
        self.assertNotIn("<iframe", html)
        self.assertIn("Merhaba", html)
        self.assertIn('loading="lazy"', html)

    def test_links_images_code(self):
        html = render(
            "[dış](https://example.com) [iç](https://ozaydin.dev/blog/) [göreli](/projeler/)\n\n"
            "![alt metin](/media/a.webp)\n\n```python\nimport os  # yorum\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
        )
        self.assertIn('href="https://example.com" target="_blank" rel="noopener"', html)
        self.assertIn('<a href="https://ozaydin.dev/blog/">', html)
        self.assertIn('<a href="/projeler/">', html)
        self.assertIn('alt="alt metin"', html)
        self.assertIn('loading="lazy"', html)
        self.assertIn('<div class="hl">', html)
        self.assertIn('<span class="kn">import</span>', html)
        self.assertIn("<table>", html)

    def test_entities_kept_escaped(self):
        self.assertEqual(clean("<p>a &lt;b&gt; &amp; c</p>"), "<p>a &lt;b&gt; &amp; c</p>")
        self.assertNotIn("<b>", render("`<b>kod</b>`"))


class ModelTests(TestCase):
    def test_reading_minutes(self):
        with translation.override("tr"):
            self.assertEqual(Post(body_tr="kısa").reading_minutes, 1)
            self.assertEqual(Post(body_tr="").reading_minutes, 1)
            self.assertEqual(Post(body_tr=" ".join(["kelime"] * 401)).reading_minutes, 3)
            self.assertEqual(Post(body_tr=" ".join(["kelime"] * 400)).reading_minutes, 2)

    def test_html_rendered_on_save(self):
        p = make_post("html", body_tr="**kalın**", body_en="")
        self.assertIn("<strong>kalın</strong>", p.body_html_tr)
        self.assertEqual(p.body_html_en, "")
        self.assertEqual(p.get_absolute_url("en"), "/en/blog/html/")

    def test_seed_post_is_draft(self):
        # 0002_ilk_yazi migration'ı: taslak, iki dilli, etiketli
        p = Post.objects.get(slug="ozaydin-devi-nasil-yayina-aldim")
        self.assertEqual(p.status, Post.Status.DRAFT)
        self.assertIn('<div class="hl">', p.body_html_tr)
        self.assertEqual(sorted(p.tags.values_list("slug", flat=True)), ["django", "sunucu"])


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ImageTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        from django.conf import settings
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def _png(self, size):
        buf = BytesIO()
        Image.new("RGB", size, (20, 20, 20)).save(buf, "PNG")
        return SimpleUploadedFile("resim.png", buf.getvalue(), content_type="image/png")

    def test_cover_and_post_image_to_webp(self):
        p = make_post("kapak", cover=self._png((3000, 1000)))
        self.assertTrue(p.cover.name.endswith(".webp"))
        c = Client(HTTP_HOST="localhost")
        r = c.get("/blog/kapak/")
        self.assertTrue(r.context["og_image"].startswith("http://localhost/media/blog/covers/"))
        im = PostImage.objects.create(post=p, image=self._png((2400, 1200)), alt_tr="ekran [görüntüsü]")
        self.assertTrue(im.image.name.endswith(".webp"))
        self.assertEqual((im.width, im.height), (1600, 800))
        self.assertEqual(im.markdown(), f"![ekran görüntüsü]({im.image.url})")
