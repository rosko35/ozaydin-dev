from django.db import models


class LoginAttempt(models.Model):
    """Başarısız yönetici girişi denemesi (IP başına). Küçük bir tablo; eski kayıtlar kendiliğinden silinir."""

    ip = models.CharField("IP", max_length=64, db_index=True)
    created_at = models.DateTimeField("zaman", auto_now_add=True)
    blocked_until = models.DateTimeField("engel bitişi", null=True, blank=True)

    class Meta:
        verbose_name = "başarısız giriş"
        verbose_name_plural = "başarısız girişler"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["ip", "created_at"])]

    def __str__(self):
        return f"{self.ip} {self.created_at:%Y-%m-%d %H:%M:%S}"
