from functools import cached_property

from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse

from core.images import to_webp


class Category(models.Model):
    """Projelerin alanı (Oyun, Backend, Web…). Projeler sayfasındaki filtre düğmeleri bunlardan oluşur."""

    name_tr = models.CharField("ad (TR)", max_length=40)
    name_en = models.CharField("ad (EN)", max_length=40, blank=True)
    slug = models.SlugField(unique=True)
    order = models.PositiveSmallIntegerField("sıra", default=0)

    class Meta:
        ordering = ["order", "name_tr"]
        verbose_name = "alan"
        verbose_name_plural = "alanlar"

    def __str__(self):
        return self.name_tr


class Project(models.Model):
    number = models.PositiveSmallIntegerField(
        "numara", unique=True, help_text="Sıra numarası. Sitede ikilik olarak görünür: 1 → 001, 2 → 010, 3 → 011."
    )
    title = models.CharField("ad", max_length=80)
    slug = models.SlugField("adres", unique=True, help_text="Adreste görünür: ozaydin.dev/projeler/projenin-adresi/")
    year = models.PositiveSmallIntegerField("yıl", null=True, blank=True)
    categories = models.ManyToManyField(Category, verbose_name="alanlar", blank=True, related_name="projects")
    stack = models.CharField("araçlar", max_length=120, blank=True, help_text="Örnek: Unity · C#")
    role_tr = models.CharField("rol (TR)", max_length=120, blank=True)
    role_en = models.CharField("rol (EN)", max_length=120, blank=True)
    duration_tr = models.CharField("süre (TR)", max_length=60, blank=True)
    duration_en = models.CharField("süre (EN)", max_length=60, blank=True)
    summary_tr = models.TextField("özet (TR)", help_text="Listede ve sayfanın başında görünen bir iki cümle.")
    summary_en = models.TextField("özet (EN)", blank=True)
    problem_tr = models.TextField("sorun (TR)", blank=True)
    problem_en = models.TextField("sorun (EN)", blank=True)
    did_tr = models.TextField("ne yaptım (TR)", blank=True, help_text="Her satır bir madde.")
    did_en = models.TextField("ne yaptım (EN)", blank=True, help_text="Her satır bir madde.")
    result_tr = models.TextField("sonuç (TR)", blank=True)
    result_en = models.TextField("sonuç (EN)", blank=True)
    flow_tr = models.TextField("akış (TR)", blank=True, help_text="Her satır bir kutu. Örnek: Tarayıcı / Nginx / Django")
    flow_en = models.TextField("akış (EN)", blank=True, help_text="Her satır bir kutu.")
    repo_url = models.URLField("kod linki", blank=True)
    live_url = models.URLField("canlı link", blank=True)
    cover = models.ImageField(
        "kapak görseli", upload_to="projects/covers/", blank=True,
        help_text="İsteğe bağlı. Yoksa projenin adından üretilen bit şeridi kullanılır.",
    )
    video = models.FileField(
        "demo videosu", upload_to="projects/videos/", blank=True,
        validators=[FileExtensionValidator(["mp4", "webm"])],
        help_text="İsteğe bağlı. MP4 (H.264) ya da WebM, en fazla 200 MB; 50 MB altı önerilir. "
                  "Varsa proje sayfasının en üstünde oynatıcı olarak görünür.",
    )
    video_poster = models.ImageField(
        "video kapak resmi", upload_to="projects/videos/", blank=True,
        help_text="İsteğe bağlı. Video oynatılmadan önce görünen kare. Boşsa kapak görseli kullanılır.",
    )
    # Proje dizinindeki kart için küçük kopya (WebP, 640 px genişlik). Kendiliğinden üretilir.
    card_thumb = models.ImageField(upload_to="projects/cards/", blank=True, editable=False)
    card_thumb_src = models.CharField(max_length=255, blank=True, editable=False)
    card_w = models.PositiveIntegerField(default=0, editable=False)
    card_h = models.PositiveIntegerField(default=0, editable=False)
    featured = models.BooleanField("ana sayfada göster", default=True)
    is_published = models.BooleanField("yayında", default=True)
    updated = models.DateTimeField("güncellendi", auto_now=True)

    class Meta:
        ordering = ["number"]
        verbose_name = "proje"
        verbose_name_plural = "projeler"

    def __str__(self):
        return f"{self.idx} · {self.title}"

    @property
    def idx(self):
        """İkilik numara, en az 3 hane: 1 → '001'."""
        return format(self.number, "03b")

    CARD_WIDTH = 640

    def card_source(self):
        """Proje dizininde satırın görseli: kapak, yoksa video kapağı, yoksa ilk galeri görseli (ya da None)."""
        for f in (self.cover, self.video_poster):
            if f:
                return f
        im = self.images.first()
        return im.image if im and im.image else None

    def ensure_card_thumb(self):
        """Kart görselinin küçük kopyası yoksa ya da kaynak değiştiyse üretir. Kopyayı döndürür (ya da None).
        Kayıt update() ile yazılır: 'güncellendi' tarihi değişmez, save() tetiklenmez."""
        src = self.card_source()
        if not src:
            return None
        thumb = self.card_thumb
        if thumb and self.card_thumb_src == src.name and thumb.storage.exists(thumb.name):
            return thumb
        content, (w, h) = to_webp(src, self.CARD_WIDTH, quality=80, width=self.CARD_WIDTH)
        old = thumb.name if thumb else ""
        name = thumb.storage.save(thumb.field.generate_filename(self, f"{self.slug}-{content.name}"), content)
        self.card_thumb.name, self.card_thumb_src, self.card_w, self.card_h = name, src.name, w, h
        if self.pk:
            type(self).objects.filter(pk=self.pk).update(card_thumb=name, card_thumb_src=src.name, card_w=w, card_h=h)
        if old and old != name:
            thumb.storage.delete(old)
        return self.card_thumb

    @cached_property
    def card_image(self):
        """Satırın görseli (küçük WebP kopya). Hiç görsel yoksa None: o satırda kart çıkmaz."""
        try:
            thumb = self.ensure_card_thumb()
        except (OSError, ValueError, SyntaxError):
            thumb = None
        if thumb:
            return {"url": thumb.url, "w": self.card_w, "h": self.card_h}
        # Küçük kopya üretilemediyse (bozuk dosya, disk izni) eldeki görsel kullanılır.
        for f in (self.cover, self.video_poster):
            if f:
                try:
                    return {"url": f.url, "w": f.width, "h": f.height}
                except (OSError, ValueError):
                    continue
        im = self.images.first()
        if im and im.image:
            src = im.thumb or im.image
            return {"url": src.url, "w": im.width or 800, "h": im.height or 600}
        return None

    def get_absolute_url(self, lang="tr"):
        return reverse(f"{lang}:project", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if self.cover and not getattr(self.cover, "_committed", True):
            content, _ = to_webp(self.cover, 2000)
            self.cover.save(content.name, content, save=False)
        if self.video_poster and not getattr(self.video_poster, "_committed", True):
            content, _ = to_webp(self.video_poster, 1920)
            self.video_poster.save(content.name, content, save=False)
        super().save(*args, **kwargs)


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images", verbose_name="proje")
    image = models.ImageField("görsel", upload_to="projects/gallery/")
    thumb = models.ImageField(upload_to="projects/gallery/thumbs/", blank=True, editable=False)
    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)
    caption_tr = models.CharField("açıklama (TR)", max_length=200, blank=True)
    caption_en = models.CharField("açıklama (EN)", max_length=200, blank=True)
    order = models.PositiveSmallIntegerField("sıra", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "görsel"
        verbose_name_plural = "görseller"

    def __str__(self):
        return self.caption_tr or self.image.name

    def save(self, *args, **kwargs):
        # Yeni yüklenen görsel: büyük hâli en fazla 2000 px, küçük hâli 800 px, ikisi de WebP.
        if self.image and (not self.thumb or not getattr(self.image, "_committed", True)):
            full, size = to_webp(self.image, 2000)
            small, _ = to_webp(self.image, 800)
            self.image.save(full.name, full, save=False)
            self.thumb.save(small.name, small, save=False)
            self.width, self.height = size
        super().save(*args, **kwargs)
