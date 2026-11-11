from django.db import models


class Message(models.Model):
    """İletişim formundan gelen mesaj."""

    LANGS = [("tr", "Türkçe"), ("en", "English")]

    name = models.CharField("ad", max_length=100)
    email = models.EmailField("e-posta", max_length=200)
    body = models.TextField("mesaj")
    lang = models.CharField("dil", max_length=2, choices=LANGS, default="tr")
    created = models.DateTimeField("tarih", auto_now_add=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("tarayıcı", max_length=300, blank=True)
    is_read = models.BooleanField("okundu", default=False)
    is_spam = models.BooleanField("spam", default=False)
    emailed = models.BooleanField("bildirim gitti", default=False)

    class Meta:
        ordering = ["-created"]
        verbose_name = "mesaj"
        verbose_name_plural = "mesajlar"
        indexes = [models.Index(fields=["ip", "created"])]

    def __str__(self):
        return f"{self.name} <{self.email}>"
