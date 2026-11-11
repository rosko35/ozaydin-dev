"""
Yazı gövdesini (Markdown) HTML'e çevirir ve çıktıyı temizler.

Yazar sadece Emre, yine de çıktı her zaman temizleyiciden geçer: <script>, <iframe> gibi
etiketler içerikleriyle atılır, on* öznitelikleri ve javascript: linkleri silinir.
Aynı geçişte dış linklere target/rel, görsellere loading="lazy" eklenir.
"""
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit

import markdown as md
from markdown.extensions.toc import slugify as _ascii_slugify

SITE_HOSTS = {"ozaydin.dev", "www.ozaydin.dev"}

# İçeriğiyle birlikte atılan etiketler
DROP_WITH_CONTENT = {"script", "style", "iframe", "object", "embed", "noscript", "template", "frame", "frameset", "svg", "math"}
# Sadece etiketi atılan (içindeki metin kalır)
DROP_TAG = {"form", "input", "button", "textarea", "select", "option", "link", "meta", "base", "html", "head", "body", "applet"}
URL_ATTRS = {"href", "src", "action", "formaction", "xlink:href", "poster", "background", "srcset"}
SAFE_SCHEMES = {"http", "https", "mailto", "tel", ""}
VOID = {"area", "br", "col", "hr", "img", "source", "track", "wbr"}

_TR = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")


def slugify(value, separator):
    """Başlık id'leri: Türkçe harfler sadeleşir ('Ağ ayarları' → 'ag-ayarlari')."""
    return _ascii_slugify(value.translate(_TR), separator)


def _safe_url(value):
    v = "".join(ch for ch in (value or "") if ch > " ").lower()  # boşluk ve kontrol karakterleri atlatma için kullanılabilir
    scheme = v.split(":", 1)[0] if ":" in v.split("/", 1)[0] else ""
    return scheme in SAFE_SCHEMES


def _is_external(href):
    try:
        parts = urlsplit(href)
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and (parts.hostname or "") not in SITE_HOSTS


class _Cleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out = []
        self.skip = 0  # DROP_WITH_CONTENT içinde miyiz (iç içe sayaç)

    def _attrs(self, tag, attrs):
        kept = {}
        for name, value in attrs:
            name = name.lower()
            if name.startswith("on") or name in ("style", "srcdoc", "formaction"):
                continue
            if name in URL_ATTRS and not _safe_url(value):
                continue
            kept[name] = "" if value is None else value
        if tag == "a" and _is_external(kept.get("href", "")):
            kept["target"] = "_blank"
            kept["rel"] = "noopener"
        if tag == "img":
            kept["loading"] = "lazy"
            kept.setdefault("alt", "")
            kept.setdefault("decoding", "async")
        return "".join(f' {k}="{escape(v, quote=True)}"' for k, v in kept.items())

    def handle_starttag(self, tag, attrs, closed=False):
        if tag in DROP_WITH_CONTENT:
            if not closed and tag not in VOID:
                self.skip += 1
            return
        if self.skip or tag in DROP_TAG:
            return
        self.out.append(f"<{tag}{self._attrs(tag, attrs)}{' /' if closed else ''}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, closed=True)

    def handle_endtag(self, tag):
        if tag in DROP_WITH_CONTENT:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip or tag in DROP_TAG or tag in VOID:
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(escape(data, quote=False))

    def handle_entityref(self, name):
        if not self.skip:
            self.out.append(f"&{name};")

    def handle_charref(self, name):
        if not self.skip:
            self.out.append(f"&#{name};")

    # Yorumlar, <!doctype>, <?...?> atılır.
    def handle_comment(self, data):
        pass

    def handle_decl(self, decl):
        pass

    def handle_pi(self, data):
        pass

    def unknown_decl(self, data):
        pass


def clean(html):
    """HTML'den tehlikeli etiket/öznitelikleri atar; dış linklere target/rel, görsellere lazy ekler."""
    p = _Cleaner()
    p.feed(html or "")
    p.close()
    return "".join(p.out)


def render(text):
    """Markdown → temiz HTML."""
    if not (text or "").strip():
        return ""
    converter = md.Markdown(
        extensions=["fenced_code", "codehilite", "tables", "toc", "sane_lists"],
        extension_configs={
            "codehilite": {"css_class": "hl", "guess_lang": False, "use_pygments": True, "noclasses": False},
            "toc": {"slugify": slugify, "permalink": False},
        },
        output_format="html",
    )
    return clean(converter.convert(text))
