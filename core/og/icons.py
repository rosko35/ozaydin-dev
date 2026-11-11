"""
Site ikonlarını üretir (base.html'deki SVG ikonla aynı tasarım: koyu zemin, beyaz "01").
Tasarım değişirse yeniden çalıştır:
    python -m core.og.icons core/static/core/icons
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from .render import BG_0, INK, font


def icon(size, rounded=True):
    """size×size ikon. rounded: köşeler şeffaf ve yuvarlak (favicon); değilse tam kare (Apple, manifest)."""
    s = 8  # büyük çizip küçült: kenarlar yumuşak olsun
    big = size * s
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle((0, 0, big - 1, big - 1), radius=big * 6 // 32, fill=BG_0)
    else:
        d.rectangle((0, 0, big, big), fill=BG_0)
    # Kare ikonlarda (Apple, maskable) yazı güvenli alanda kalsın diye biraz küçük
    fnt = font("GeistMono-Medium.ttf", int(big * (15 / 32 if rounded else 0.40)))
    d.text((big / 2, big / 2), "01", font=fnt, fill=INK, anchor="mm")
    return img.resize((size, size), Image.Resampling.LANCZOS)


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    icon(32).save(out / "favicon-32.png", optimize=True)
    icon(180, rounded=False).convert("RGB").save(out / "apple-touch-icon.png", optimize=True)
    icon(192, rounded=False).convert("RGB").save(out / "icon-192.png", optimize=True)
    icon(512, rounded=False).convert("RGB").save(out / "icon-512.png", optimize=True)
    icon(48).save(out / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "core/static/core/icons")
