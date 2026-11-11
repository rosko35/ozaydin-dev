from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from core.routes import lreverse
from core.translate import tfield, ui as ui_text

register = template.Library()


@register.simple_tag
def ui(key, **kw):
    """{% ui "nav.projects" %}: arayüz metni. Metinler core/i18n.py'de; içlerindeki <b> gibi basit HTML bilerek korunur."""
    return mark_safe(ui_text(key, **kw))


@register.simple_tag
def lurl(name, **kwargs):
    """{% lurl "project" slug=p.slug %}: adresin şu anki dildeki hâli."""
    return lreverse(name, **kwargs)


@register.filter
def t(obj, field):
    """{{ p|t:"summary" }}: çift dilli alanın şu anki dildeki değeri."""
    return tfield(obj, field)


@register.filter
def lines(text):
    """Her satırı bir madde olarak böler, boş satırları atar."""
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


@register.simple_tag
def tape(name, height=None):
    """Adın UTF-8 baytlarından 'delikli şerit' SVG: her sütun bir bayt, üst satır en anlamlı bit."""
    data = name.encode("utf-8")
    cw = 12
    parts = [
        f'<span class="tape"><svg viewBox="0 0 {len(data) * cw} {8 * cw}" role="img" '
        f'aria-label="{escape(name)} · {len(data)} bayt"'
        + (f' style="height:{int(height)}px;width:auto"' if height else "")
        + ">"
    ]
    for c, v in enumerate(data):
        for r in range(8):
            x, y = c * cw, r * cw
            if (v >> (7 - r)) & 1:
                parts.append(f'<rect class="t1" x="{x + 2}" y="{y + 2}" width="8" height="8" rx="2"/>')
            else:
                parts.append(f'<circle class="t0" cx="{x + 6}" cy="{y + 6}" r="1.25"/>')
    parts.append("</svg></span>")
    return mark_safe("".join(parts))


@register.filter
def nbytes(name):
    return len((name or "").encode("utf-8"))


@register.filter
def binary(n):
    """10 → '1010'."""
    try:
        return format(int(n), "b")
    except (TypeError, ValueError):
        return ""
