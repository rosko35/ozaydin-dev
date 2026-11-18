"""Proje dizini kartları için küçük WebP kopyaları üretir (eksik ya da eskimiş olanları).
Site bunları ilk ihtiyaçta kendisi de üretir; bu komut güncellemede önceden hazırlamak için.
    python manage.py kart_gorselleri
"""
from django.core.management.base import BaseCommand

from projects.models import Project


class Command(BaseCommand):
    help = "Proje kartları için küçük WebP görselleri üretir."

    def handle(self, *args, **options):
        made = 0
        for p in Project.objects.all():
            before = (p.card_thumb.name, p.card_thumb_src)
            try:
                p.ensure_card_thumb()
            except (OSError, ValueError, SyntaxError) as e:
                self.stderr.write(f"{p.slug}: {e}")
                continue
            if (p.card_thumb.name, p.card_thumb_src) != before:
                made += 1
        self.stdout.write(f"Kart görselleri: {made} yeni")
