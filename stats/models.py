from django.db import models


class DailyPage(models.Model):
    """Günlük sayfa sayacı. `unique`: o gün siteye ilk kez bu sayfadan giren ziyaretçi sayısı
    (tüm sayfaların toplamı = günlük benzersiz ziyaretçi)."""

    date = models.DateField("tarih", db_index=True)
    path = models.CharField("sayfa", max_length=200)
    lang = models.CharField("dil", max_length=2)
    views = models.PositiveIntegerField("görüntüleme", default=0)
    unique = models.PositiveIntegerField("benzersiz", default=0)

    class Meta:
        verbose_name = "sayfa istatistiği"
        verbose_name_plural = "sayfa istatistikleri"
        ordering = ("-date", "-views")
        constraints = [models.UniqueConstraint(fields=("date", "path"), name="stats_dailypage_date_path")]

    def __str__(self):
        return f"{self.date} {self.path}"


class DailyVisitor(models.Model):
    """Günlük tuzlu özet; ertesi gün eşleştirilemez. 2 günden eskiler silinir."""

    date = models.DateField(db_index=True)
    hash = models.CharField(max_length=64)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("date", "hash"), name="stats_dailyvisitor_date_hash")]


class DailyReferrer(models.Model):
    date = models.DateField("tarih", db_index=True)
    host = models.CharField("site", max_length=200)
    count = models.PositiveIntegerField("sayı", default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("date", "host"), name="stats_dailyreferrer_date_host")]
