from django.utils.translation import get_language

from .i18n import STRINGS


def lang():
    return "en" if get_language() == "en" else "tr"


def ui(key, **kw):
    """Arayüz metni, şu anki dilde. Bilinmeyen anahtar olduğu gibi döner (hatayı fark etmek kolay olsun)."""
    pair = STRINGS.get(key)
    text = key if pair is None else pair[1 if lang() == "en" else 0]
    return text.format(**kw) if kw else text


def tfield(obj, field):
    """Modeldeki çift dilli alan: İngilizce sayfada <alan>_en doluysa onu, değilse <alan>_tr'yi döndürür."""
    if lang() == "en":
        val = getattr(obj, f"{field}_en", "")
        if val:
            return val
    return getattr(obj, f"{field}_tr", "")
