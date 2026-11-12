"""
Yapay zekâ servisleri. Sunucudaki ayarla seçilir (DJANGO_CHAT_PROVIDER):
  gemini     Google Gemini (AI Studio anahtarı)
  anthropic  Claude
Ek paket gerekmez; istekler doğrudan HTTPS ile gider.
"""
import json
import urllib.error
import urllib.request

from django.conf import settings


class ProviderError(Exception):
    pass


def _post(url, headers, body, timeout=25):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="ignore")[:300]
        raise ProviderError(f"HTTP {e.code}: {detail}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise ProviderError(f"bağlantı: {e}") from e


def gemini(system, history, max_tokens):
    model = settings.CHAT_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["text"]}]} for m in history]
    data = _post(url, {"x-goog-api-key": settings.CHAT_API_KEY}, {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.4},
    })
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    except (KeyError, IndexError):
        raise ProviderError("boş cevap: " + json.dumps(data)[:200])


def anthropic(system, history, max_tokens):
    data = _post("https://api.anthropic.com/v1/messages", {
        "x-api-key": settings.CHAT_API_KEY, "anthropic-version": "2023-06-01",
    }, {
        "model": settings.CHAT_MODEL, "max_tokens": max_tokens, "system": system,
        "messages": [{"role": "user" if m["role"] == "user" else "assistant", "content": m["text"]} for m in history],
    })
    try:
        return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text").strip()
    except KeyError:
        raise ProviderError("boş cevap")


PROVIDERS = ("gemini", "anthropic")


def ask(system, history, max_tokens=700):
    fn = globals().get(settings.CHAT_PROVIDER) if settings.CHAT_PROVIDER in PROVIDERS else None
    if not fn or not settings.CHAT_API_KEY:
        raise ProviderError("asistan ayarlı değil")
    text = fn(system, history, max_tokens)
    if not text:
        raise ProviderError("boş cevap")
    return text
