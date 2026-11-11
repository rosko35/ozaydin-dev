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
    slug = models.SlugField("adres", unique=True, help_text="Adreste görünür: ozaydin.dev/projeler/<adres>/")
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
    featured = models.BooleanField("ana sayfada göster", default=True)
    is_published = models.BooleanField("yayında", default=True)
    updated = models.DateTimeField(auto_now=True)

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

    def get_absolute_url(self, lang="tr"):
        return reverse(f"{lang}:project", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if self.cover and not getattr(self.cover, "_committed", True):
            content, _ = to_webp(self.cover, 2000)
            self.cover.save(content.name, content, save=False)
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
