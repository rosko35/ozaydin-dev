import math
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.images import to_webp
from core.translate import lang

from .markdown import render

MD_HELP = (
    "Markdown: **kalın**, `kod`, ```python blok```, ## başlık, [link](adres), ![alt](görsel-adresi). "
    "Görsel yüklemek için sayfanın altındaki “Yazı görselleri” bölümünü kullan; kaydettikten sonra her görselin "
    "Markdown kodu orada görünür."
)

WORD = re.compile(r"\w+", re.UNICODE)
RESERVED_SLUGS = {"rss", "etiket", "tag"}  # /blog/rss/ gibi adreslerle çakışır


def not_reserved(value):
    if value in RESERVED_SLUGS:
        raise ValidationError(f"“{value}” adresi blogda başka bir sayfa için ayrılmış; başka bir adres seç.")


class Tag(models.Model):
    name_tr = models.CharField("ad (TR)", max_length=40)
    name_en = models.CharField("ad (EN)", max_length=40, blank=True)
    slug = models.SlugField("adres", unique=True, help_text="Adreste görünür: ozaydin.dev/blog/etiket/etiketin-adresi/")

    class Meta:
        ordering = ["name_tr"]
        verbose_name = "etiket"
        verbose_name_plural = "etiketler"

    def __str__(self):
        return self.name_tr

    def get_absolute_url(self, lang="tr"):
        return reverse(f"{lang}:blog_tag", kwargs={"slug": self.slug})


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Post.Status.PUBLISHED, published_at__lte=timezone.now())


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Taslak"
        PUBLISHED = "published", "Yayında"

    title_tr = models.CharField("başlık (TR)", max_length=160)
    title_en = models.CharField("başlık (EN)", max_length=160, blank=True)
    slug = models.SlugField("adres", max_length=160, unique=True, validators=[not_reserved], help_text="Adreste görünür: ozaydin.dev/blog/yazinin-adresi/")
    summary_tr = models.TextField("özet (TR)", help_text="Listede, sayfanın başında ve arama sonuçlarında görünen bir iki cümle.")
    summary_en = models.TextField("özet (EN)", blank=True)
    body_tr = models.TextField("gövde (TR)", help_text=MD_HELP)
    body_en = models.TextField(
        "gövde (EN)", blank=True,
        help_text="Boş bırakılırsa yazı İngilizce listede yine görünür; Türkçe metin “şimdilik sadece Türkçe” notuyla gösterilir. "
        + MD_HELP,
    )
    body_html_tr = models.TextField(blank=True, editable=False)
    body_html_en = models.TextField(blank=True, editable=False)
    cover = models.ImageField(
        "kapak görseli", upload_to="blog/covers/", blank=True,
        help_text="İsteğe bağlı. Otomatik küçültülür ve WebP'ye çevrilir; paylaşım önizlemesinde de kullanılır.",
    )
    tags = models.ManyToManyField(Tag, verbose_name="etiketler", blank=True, related_name="posts")
    status = models.CharField("durum", max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(
        "yayın tarihi", null=True, blank=True,
        help_text="Boş bırakıp “Yayında” seçersen kaydettiğin an yazılır. İleri bir tarih verirsen yazı o zaman görünür.",
    )
    updated = models.DateTimeField("güncellendi", auto_now=True)
    related_project = models.ForeignKey(
        "projects.Project", verbose_name="ilgili proje", null=True, blank=True, on_delete=models.SET_NULL, related_name="posts",
    )

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-id"]
        verbose_name = "yazı"
        verbose_name_plural = "yazılar"

    def __str__(self):
        return self.title_tr

    def get_absolute_url(self, lang="tr"):
        return reverse(f"{lang}:post", kwargs={"slug": self.slug})

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED and self.published_at is not None and self.published_at <= timezone.now()

    @property
    def only_tr(self):
        """İngilizce sayfada ama İngilizce gövde yok: Türkçe metin gösterilir."""
        return lang() == "en" and not self.body_en.strip()

    @property
    def body(self):
        return self.body_tr if (lang() == "tr" or self.only_tr) else self.body_en

    @property
    def body_html(self):
        """Şu anki dilde gövdenin HTML'i (EN boşsa TR). Kayıtta üretilir; eski kayıtlarda boşsa anında üretilir."""
        field = "body_html_tr" if (lang() == "tr" or self.only_tr) else "body_html_en"
        return getattr(self, field) or render(self.body)

    @property
    def body_lang(self):
        return "tr" if (lang() == "tr" or self.only_tr) else "en"

    @property
    def reading_minutes(self):
        """Dakika: kelime sayısı / 200, en az 1."""
        return max(1, math.ceil(len(WORD.findall(self.body or "")) / 200))

    def render_html(self):
        self.body_html_tr = render(self.body_tr)
        self.body_html_en = render(self.body_en)

    def save(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        if self.cover and not getattr(self.cover, "_committed", True):
            content, _ = to_webp(self.cover, 2000)
            self.cover.save(content.name, content, save=False)
        self.render_html()
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"body_html_tr", "body_html_en"}
        super().save(*args, **kwargs)


class PostImage(models.Model):
    """Yazı içinde kullanılacak görseller. Admin'de her birinin Markdown kodu kopyalanabilir."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images", verbose_name="yazı")
    image = models.ImageField("görsel", upload_to="blog/images/")
    alt_tr = models.CharField("alt metin (TR)", max_length=200, help_text="Görseli göremeyenler için kısa açıklama.")
    alt_en = models.CharField("alt metin (EN)", max_length=200, blank=True)
    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["id"]
        verbose_name = "yazı görseli"
        verbose_name_plural = "yazı görselleri"

    def __str__(self):
        return self.alt_tr or self.image.name

    def markdown(self, lang="tr"):
        alt = (self.alt_en if lang == "en" and self.alt_en else self.alt_tr).replace("[", "").replace("]", "")
        return f"![{alt}]({self.image.url})"

    def save(self, *args, **kwargs):
        if self.image and not getattr(self.image, "_committed", True):
            content, size = to_webp(self.image, 1600)
            self.image.save(content.name, content, save=False)
            self.width, self.height = size
        super().save(*args, **kwargs)
