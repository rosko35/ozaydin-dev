"""
Site ikonlarını üretir: koyu zemin (--bg), kırık beyaz "01" (Big Shoulders Display 900, addaki yazı tipi)
ve yanında asit yeşili nokta. favicon.svg de aynı tasarım; harfler yazı tipinden çizgiye çevrilir
(SVG ikon dış yazı tipi yükleyemez). Tasarım değişirse yeniden çalıştır:
    python -m core.og.icons core/static/core/icons
"""
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

from .render import BG, FG, FONTS, POSTER, SIG, font

TEXT = "01"
HEX = lambda c: "#%02X%02X%02X" % c  # noqa: E731


def _layout(box):
    """Yazı tipinden '01' glifleri ve ölçüleri. Kare ikonlarda (Apple, maskable) şekil güvenli alanda
    kalsın diye çağıran taraf daha küçük çizer."""
    f = TTFont(FONTS / POSTER)
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    names = [cmap[ord(ch)] for ch in TEXT]
    upm = f["head"].unitsPerEm
    adv = sum(gs[n].width for n in names)
    cap = f["OS/2"].sCapHeight or int(upm * 0.7)
    return f, gs, names, upm, adv, cap


def svg(rounded=True):
    """32×32 viewBox'lı SVG ikon (harfler çizgi)."""
    f, gs, names, upm, adv, cap = _layout(32)
    h = 32 * (0.62 if rounded else 0.5)
    k = h / cap
    dot = h * 0.12
    total = adv * k + dot * 2.6
    x0, base = (32 - total) / 2, (32 + h) / 2
    paths, x = [], x0
    for n in names:
        pen = SVGPathPen(gs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
        gs[n].draw(TransformPen(pen, (k, 0, 0, -k, x, base)))
        paths.append(pen.getCommands())
        x += gs[n].width * k
    cx, cy = x + dot * 1.6, base - dot
    bg = f'<rect width="32" height="32" rx="6" fill="{HEX(BG)}"/>' if rounded else f'<rect width="32" height="32" fill="{HEX(BG)}"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">{bg}'
            f'<path fill="{HEX(FG)}" d="{" ".join(paths)}"/>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{dot:.2f}" fill="{HEX(SIG)}"/></svg>')


def icon(size, rounded=True):
    """size×size PNG ikon. rounded: köşeler şeffaf ve yuvarlak (favicon); değilse tam kare (Apple, manifest)."""
    s = 8  # büyük çizip küçült: kenarlar yumuşak olsun
    big = size * s
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle((0, 0, big - 1, big - 1), radius=big * 6 // 32, fill=BG)
    else:
        d.rectangle((0, 0, big, big), fill=BG)
    f, gs, names, upm, adv, cap = _layout(big)
    h = big * (0.62 if rounded else 0.5)
    k = h / cap
    dot = h * 0.12
    total = adv * k + dot * 2.6
    x, base = (big - total) / 2, (big + h) / 2
    d.text((x, base), TEXT, font=font(POSTER, round(upm * k)), fill=FG, anchor="ls")
    cx, cy = x + adv * k + dot * 1.6, base - dot
    d.ellipse((cx - dot, cy - dot, cx + dot, cy + dot), fill=SIG)
    return img.resize((size, size), Image.Resampling.LANCZOS)


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "favicon.svg").write_text(svg() + "\n", encoding="utf-8")
    icon(32).save(out / "favicon-32.png", optimize=True)
    icon(180, rounded=False).convert("RGB").save(out / "apple-touch-icon.png", optimize=True)
    icon(192, rounded=False).convert("RGB").save(out / "icon-192.png", optimize=True)
    icon(512, rounded=False).convert("RGB").save(out / "icon-512.png", optimize=True)
    icon(48).save(out / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "core/static/core/icons")
