from django.db import models


class ChatLog(models.Model):
    """Sitedeki asistana sorulan her soru. 30 günden eskileri kendiliğinden silinir."""

    created = models.DateTimeField("zaman", auto_now_add=True, db_index=True)
    lang = models.CharField("dil", max_length=2, default="tr")
    ip_hash = models.CharField(max_length=64, db_index=True, editable=False)
    question = models.TextField("soru")
    answer = models.TextField("cevap", blank=True)
    ok = models.BooleanField("başarılı", default=True)
    error = models.CharField("hata", max_length=200, blank=True)
    ms = models.PositiveIntegerField("süre (ms)", default=0)

    class Meta:
        ordering = ["-created"]
        verbose_name = "soru"
        verbose_name_plural = "sorular"

    def __str__(self):
        return self.question[:60]
