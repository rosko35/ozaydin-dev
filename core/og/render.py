"""
OG kartı çizimi, sitenin "Düzen D" görünümüyle: koyu mürekkep zemin, kırık beyaz yazı, tek vurgu (asit yeşili nokta).
Başlık Instrument Serif; ad Big Shoulders Display 900 (sitedeki logotip gibi büyük harf); küçük etiketler Geist Mono.
Sağda başlığın UTF-8 baytlarından 0/1 sütunları (her sütun bir bayt: 1 parlak, 0 soluk).

Yazı tipleri: core/og/fonts/ (hepsi SIL OFL). Sitedeki woff2 dosyalarından fontTools ile TTF'ye çevrildi;
latin ve latin-ext alt kümeleri tek dosyada birleştirildi (ı, ş, ğ, İ için). Bu klasör statik olarak servis edilmez.
"""
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
PAD = 72
FONTS = Path(__file__).resolve().parent / "fonts"

# site.css'teki oklch() renklerinin sRGB karşılıkları
BG = (8, 13, 18)  # --bg   oklch(0.155 0.014 255)
BG_1 = (15, 19, 25)  # --bg-1 oklch(0.185 0.014 255)
BG_3 = (32, 36, 43)  # --bg-3
FG = (240, 238, 233)  # --fg   oklch(0.95 0.008 95)
G1 = (185, 190, 196)  # --g1
G2 = (141, 147, 154)  # --g2
G3 = (123, 129, 135)  # --g3
G4 = (100, 105, 112)  # --g4
SIG = (192, 244, 71)  # --sig  oklch(0.90 0.20 125)
RULE = (38, 42, 46)  # --rule: kırık beyaz %13, zemin üstünde

# Eski adlar (ikon üretici ve dışarıdan kullananlar için)
BG_0, INK = BG, FG

SERIF = "InstrumentSerif-Regular.ttf"
SERIF_IT = "InstrumentSerif-Italic.ttf"
POSTER = "BigShouldersDisplay-Black.ttf"
MONO = "GeistMono-Medium.ttf"

# Tasarım değişince artır: önbellekteki eski kartlar kullanılmaz, paylaşım adresleri de değişir.
VERSION = 2

_font_cache = {}


def font(name, size):
    key = (name, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONTS / name), size)
    return _font_cache[key]


def _background():
    # Çok hafif dikey geçiş: üst --bg, alt --bg-1 (sitedeki gibi düz ve koyu)
    grad = Image.linear_gradient("L").resize((W, H), Image.Resampling.BICUBIC)
    return Image.composite(Image.new("RGB", (W, H), BG_1), Image.new("RGB", (W, H), BG), grad)


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
    sizes = (112, 100, 90, 80, 72, 64, 58)
    for cut in (False, True):
        for size in (sizes if not cut else sizes[-1:]):
            fnt = font(SERIF, size)
            lh = int(size * 1.0)
            lines = _wrap(draw, text, fnt, max_w, max(1, min(3, max_h // lh)), cut=cut)
            if lines:
                return fnt, lh, lines
    fnt = font(SERIF, 50)
    s = text
    while s and draw.textlength(s + "…", font=fnt) > max_w:
        s = s[:-1]
    return fnt, 52, [s + "…"]


def _tape(draw, data, right, top, area_w, area_h):
    """Baytları sağa yaslanmış 0/1 sütunları olarak çizer. Çok uzunsa ilk baytlar gösterilir."""
    cell = max(22, min(36, area_h // 8))
    cols = max(1, min(len(data), area_w // cell))
    data = data[:cols]
    x0 = right - cols * cell
    y0 = top + (area_h - 8 * cell) // 2
    fnt = font(MONO, int(cell * 0.62))
    for c, v in enumerate(data):
        for r in range(8):
            on = (v >> (7 - r)) & 1
            cx, cy = x0 + c * cell + cell / 2, y0 + r * cell + cell / 2
            draw.text((cx, cy), "1" if on else "0", font=fnt, fill=FG if on else BG_3, anchor="mm")
    return x0


def _head(draw, label, kind):
    """Üst satır: yeşil nokta + etiket, sağda tür; altında ince çizgi."""
    mono = font(MONO, 22)
    r = 6
    cy = PAD + 13
    draw.ellipse((PAD, cy - r, PAD + 2 * r, cy + r), fill=SIG)
    draw.text((PAD + 2 * r + 16, cy), label, font=mono, fill=G2, anchor="lm")
    if kind:
        draw.text((W - PAD, cy), kind, font=mono, fill=G2, anchor="rm")
    draw.line((PAD, PAD + 50, W - PAD, PAD + 50), fill=RULE, width=2)


def render(title, label, footer="Emre Özaydın", kind="", tape_text=None, title_2=""):
    """Kartı çizer, PNG baytlarını döndürür.

    title: büyük başlık; label: üstteki mono etiket ("ozaydin.dev · 001"); kind: sağ üstteki tür ("PROJE");
    tape_text: şeridin kaynağı (yoksa başlık); title_2 verilirse ana sayfa düzeni: başlık iki satır
    (ikincisi italik), altta adın büyük hâli, şerit yok.
    """
    img = _background()
    draw = ImageDraw.Draw(img)
    _head(draw, label, kind)

    if title_2:
        # Ana sayfa: sitedeki giriş gibi slogan üstte, ad altta kenardan kenara.
        name = footer.upper()
        size = 200
        while size > 60:
            fnt = font(POSTER, size)
            l, t, rr, b = draw.textbbox((0, 0), name, font=fnt, anchor="ls")
            if rr - l <= W - 2 * PAD:
                break
            size -= 1
        draw.text((PAD - l, H - PAD), name, font=fnt, fill=FG, anchor="ls")
        max_w = W - 2 * PAD
        for size in range(80, 40, -4):
            s1, s2 = font(SERIF, size), font(SERIF_IT, size)
            if draw.textlength(title, font=s1) <= max_w and draw.textlength(title_2, font=s2) <= max_w:
                break
        y = PAD + 96
        draw.text((PAD, y), title, font=s1, fill=FG, anchor="la")
        draw.text((PAD, y + int(size * 0.98)), title_2, font=s2, fill=G1, anchor="la")
    else:
        tape_bytes = (tape_text or title).encode("utf-8")
        body_top, body_bottom = PAD + 84, H - PAD - 92
        tape_left = _tape(draw, tape_bytes, W - PAD, body_top, 380, body_bottom - body_top)
        text_w = tape_left - PAD - 56
        fnt, lh, lines = _fit_title(draw, title, text_w, body_bottom - body_top)
        # Satırları serif'in büyük harf yüksekliğine göre dikeyde ortala
        block_h = lh * (len(lines) - 1) + int(fnt.size * 0.72)
        y = body_top + (body_bottom - body_top - block_h) // 2 + int(fnt.size * 0.72)
        for ln in lines:
            draw.text((PAD, y), ln, font=fnt, fill=FG, anchor="ls")
            y += lh

        draw.line((PAD, H - PAD - 60, W - PAD, H - PAD - 60), fill=RULE, width=2)
        draw.text((PAD, H - PAD + 2), footer.upper(), font=font(POSTER, 46), fill=FG, anchor="ls")
        draw.text((W - PAD, H - PAD - 4), "ozaydin.dev", font=font(MONO, 22), fill=G3, anchor="rs")

    buf = BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()
