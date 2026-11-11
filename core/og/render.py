"""
OG kartı çizimi. Sitenin "Bit" tasarımı: koyu lacivert zemin, solda büyük başlık,
sağda başlığın UTF-8 baytlarından delikli şerit (her sütun bir bayt, 1 = dolu kare, 0 = nokta).

Yazı tipleri: core/og/fonts/ (Geist, OFL). Sitedeki woff2 dosyalarından fontTools ile TTF'ye çevrildi;
latin ve latin-ext alt kümeleri tek dosyada birleştirildi (ı, ş, ğ, İ için).
"""
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
PAD = 72
FONTS = Path(__file__).resolve().parent / "fonts"

BG_0 = (2, 4, 10)  # --bg-0
BG_2 = (10, 17, 34)  # --bg-2
INK = (241, 243, 248)  # --ink
INK_2 = (163, 171, 187)  # --ink-2
INK_3 = (122, 131, 151)  # --ink-3
INK_4 = (59, 68, 88)  # --ink-4
LINE = (36, 40, 50)  # --line zemin üzerinde

# Tasarım değişince artır: önbellekteki eski kartlar kullanılmaz.
VERSION = 1

_font_cache = {}


def font(name, size):
    key = (name, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONTS / name), size)
    return _font_cache[key]


def _background():
    # Yumuşak çapraz geçiş: sol üst #02040A → sağ alt #0A1122 (yatay ve dikey geçişin ortalaması)
    v = Image.linear_gradient("L").resize((W, H), Image.Resampling.BICUBIC)
    h = Image.linear_gradient("L").rotate(90).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    h = h.resize((W, H), Image.Resampling.BICUBIC)
    grad = Image.blend(v, h, 0.5)
    return Image.composite(Image.new("RGB", (W, H), BG_2), Image.new("RGB", (W, H), BG_0), grad)


def _wrap(draw, text, fnt, max_w, max_lines, cut=True):
    """Metni kelime kelime satırlara böler. Sığmazsa son satır '…' ile biter (cut=False: None döner).
    None: tek bir kelime bile satıra sığmıyor."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
            continue
        if not cur:  # tek kelime satırdan uzun
            return None
        lines.append(cur)
        cur = w
        if draw.textlength(cur, font=fnt) > max_w:
            return None
    if cur:
        lines.append(cur)
    if len(lines) <= max_lines:
        return lines
    if not cut:
        return None
    kept = lines[:max_lines]
    last = kept[-1]
    while last and draw.textlength(last + "…", font=fnt) > max_w:
        last = last[:-1].rstrip()
    kept[-1] = last + "…"
    return kept


def _fit_title(draw, text, max_w, max_h):
    """Önce metnin tamamını en büyük boyutta sığdırmayı dener; olmazsa en küçük boyutta 3 satırda keser."""
    sizes = (84, 76, 68, 60, 54, 48)
    for cut in (False, True):
        for size in (sizes if not cut else sizes[-1:]):
            fnt = font("Geist-SemiBold.ttf", size)
            lh = int(size * 1.1)
            lines = _wrap(draw, text, fnt, max_w, max(1, min(3, max_h // lh)), cut=cut)
            if lines:
                return fnt, lh, lines
    fnt = font("Geist-SemiBold.ttf", 42)
    s = text
    while s and draw.textlength(s + "…", font=fnt) > max_w:
        s = s[:-1]
    return fnt, int(42 * 1.08), [s + "…"]


def _tape(draw, data, right, top, area_w, area_h):
    """Baytları sağa yaslanmış sütunlar olarak çizer. Çok uzunsa ilk baytlar gösterilir."""
    cell = max(20, min(40, area_h // 8))
    cols = max(1, min(len(data), area_w // cell))
    data = data[:cols]
    x0 = right - cols * cell
    y0 = top + (area_h - 8 * cell) // 2
    sq = int(cell * 0.66)
    off = (cell - sq) // 2
    dot = max(2, cell // 12)
    for c, v in enumerate(data):
        for r in range(8):
            x, y = x0 + c * cell, y0 + r * cell
            if (v >> (7 - r)) & 1:
                draw.rounded_rectangle((x + off, y + off, x + off + sq, y + off + sq), radius=max(2, sq // 5), fill=INK)
            else:
                cx, cy = x + cell // 2, y + cell // 2
                draw.ellipse((cx - dot, cy - dot, cx + dot, cy + dot), fill=INK_4)
    return x0


def render(title, label, footer="Emre Özaydın", kind="", tape_text=None):
    """Kartı çizer, PNG baytlarını döndürür.

    title: büyük başlık; label: üstteki mono etiket ("ozaydin.dev · 001");
    kind: sağ alttaki küçük mono etiket ("PROJE"); tape_text: şeridin kaynağı (yoksa başlık).
    """
    img = _background()
    draw = ImageDraw.Draw(img)

    mono = font("GeistMono-Medium.ttf", 24)
    draw.text((PAD, PAD), label, font=mono, fill=INK_3)
    draw.line((PAD, PAD + 52, W - PAD, PAD + 52), fill=LINE, width=2)

    # Sağda şerit, solda başlık
    tape_bytes = (tape_text or title).encode("utf-8")
    body_top, body_bottom = PAD + 96, H - PAD - 88
    tape_left = _tape(draw, tape_bytes, W - PAD, body_top, 400, body_bottom - body_top)
    text_w = tape_left - PAD - 56

    fnt, lh, lines = _fit_title(draw, title, text_w, body_bottom - body_top)
    block_h = lh * len(lines)
    y = body_top + (body_bottom - body_top - block_h) // 2
    for ln in lines:
        draw.text((PAD, y), ln, font=fnt, fill=INK)
        y += lh

    draw.line((PAD, H - PAD - 52, W - PAD, H - PAD - 52), fill=LINE, width=2)
    draw.text((PAD, H - PAD - 30), footer, font=font("Geist-Regular.ttf", 30), fill=INK_2)
    if kind:
        kw = draw.textlength(kind, font=mono)
        draw.text((W - PAD - kw, H - PAD - 26), kind, font=mono, fill=INK_3)

    buf = BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()
