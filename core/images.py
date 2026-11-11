"""Yüklenen görselleri küçültüp WebP'ye çevirir; site hızlı kalsın, disk dolmasın."""
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def to_webp(field_file, max_side, quality=82):
    """ImageField içeriğini en uzun kenarı max_side olacak şekilde küçültür, WebP ContentFile döndürür."""
    field_file.open("rb")
    img = Image.open(field_file)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, "WEBP", quality=quality, method=6)
    name = Path(field_file.name).stem + ".webp"
    return ContentFile(buf.getvalue(), name=name), img.size
