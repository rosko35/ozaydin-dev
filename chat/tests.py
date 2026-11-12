import json
from datetime import timedelta
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from . import providers, views
from .knowledge import _cache, system_prompt
from .models import ChatLog

ON = dict(CHAT_PROVIDER="gemini", CHAT_API_KEY="test-key", CHAT_MODEL="m")


class ChatTests(TestCase):
    def post(self, body, origin="http://localhost", **extra):
        headers = {"HTTP_HOST": "localhost"}
        if origin:
            headers["HTTP_ORIGIN"] = origin
        return self.client.post("/api/chat/", json.dumps(body), content_type="application/json", **headers, **extra)

    def test_off_by_default_hides_button_and_refuses(self):
        r = self.client.get("/", HTTP_HOST="localhost")
        self.assertNotContains(r, 'id="chat-fab"')
        self.assertEqual(self.post({"message": "Merhaba"}).status_code, 503)

    @override_settings(**ON)
    def test_button_shown_when_enabled(self):
        r = self.client.get("/en/", HTTP_HOST="localhost")
        self.assertContains(r, 'id="chat-fab"')
        self.assertContains(r, "Ask about Emre")

    @override_settings(**ON)
    def test_answer_and_log(self):
        with mock.patch.object(providers, "gemini", return_value="Safe City: 2072 ve ozaydin.dev.") as g:
            r = self.post({"message": "  Hangi   projeler? ", "history": [{"role": "bot", "text": "Merhaba"}], "lang": "tr"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"ok": True, "answer": "Safe City: 2072 ve ozaydin.dev."})
        system, history, _ = g.call_args.args
        self.assertIn("Safe City: 2072", system)
        self.assertEqual(history, [{"role": "user", "text": "Hangi projeler?"}])  # bot ile başlayan geçmiş kırpılır
        log = ChatLog.objects.get()
        self.assertTrue(log.ok)
        self.assertNotIn("127.0.0.1", log.ip_hash)

    @override_settings(**ON)
    def test_requires_same_origin_and_json(self):
        self.assertEqual(self.post({"message": "x"}, origin="https://kotu.example").status_code, 403)
        self.assertEqual(self.post({"message": "x"}, origin=None).status_code, 403)
        r = self.client.post("/api/chat/", {"message": "x"}, HTTP_HOST="localhost", HTTP_ORIGIN="http://localhost")
        self.assertIn(r.status_code, (400, 403))
        self.assertEqual(self.client.get("/api/chat/", HTTP_HOST="localhost").status_code, 405)

    @override_settings(**ON)
    def test_empty_and_long(self):
        self.assertEqual(self.post({"message": "   "}).status_code, 400)
        with mock.patch.object(providers, "gemini", return_value="ok") as g:
            self.post({"message": "a" * 2000})
        self.assertEqual(len(g.call_args.args[1][-1]["text"]), views.MAX_CHARS)

    @override_settings(**ON)
    def test_rate_limits(self):
        with mock.patch.object(providers, "gemini", return_value="ok"):
            for _ in range(views.PER_HOUR):
                self.assertEqual(self.post({"message": "soru"}).status_code, 200)
            r = self.post({"message": "soru", "lang": "en"})
        self.assertEqual(r.status_code, 429)
        self.assertIn("try again later", r.json()["message"])

    @override_settings(**ON)
    def test_site_daily_cap(self):
        ChatLog.objects.bulk_create([ChatLog(ip_hash=str(i), question="q") for i in range(views.SITE_PER_DAY)])
        self.assertEqual(self.post({"message": "soru"}).status_code, 429)

    @override_settings(**ON)
    def test_provider_error_logged_not_leaked(self):
        with mock.patch.object(providers, "gemini", side_effect=providers.ProviderError("HTTP 500: gizli ayrıntı")):
            r = self.post({"message": "soru"})
        self.assertEqual(r.status_code, 502)
        self.assertNotIn("gizli", r.content.decode())
        self.assertFalse(ChatLog.objects.get().ok)

    @override_settings(**ON)
    def test_old_logs_deleted(self):
        old = ChatLog.objects.create(ip_hash="x", question="eski")
        ChatLog.objects.filter(pk=old.pk).update(created=timezone.now() - timedelta(days=31))
        with mock.patch.object(providers, "gemini", return_value="ok"):
            self.post({"message": "yeni"})
        self.assertFalse(ChatLog.objects.filter(pk=old.pk).exists())

    def test_prompt_has_profile_and_rules(self):
        _cache["t"] = 0
        p = system_prompt()
        self.assertIn("Doğu Akdeniz", p)
        self.assertIn("uydurma", p)
        self.assertNotIn("+90", p)


class GeminiRequestTests(TestCase):
    @override_settings(**ON)
    def test_request_shape(self):
        sent = {}

        def fake(url, headers, body, timeout=25):
            sent.update(url=url, headers=headers, body=body)
            return {"candidates": [{"content": {"parts": [{"text": "düşünce", "thought": True}, {"text": "Cevap"}]}}]}

        with mock.patch.object(providers, "_post", fake):
            out = providers.ask("sistem", [{"role": "user", "text": "s"}, {"role": "bot", "text": "c"}, {"role": "user", "text": "s2"}])
        self.assertEqual(out, "Cevap")
        self.assertIn("/models/m:generateContent", sent["url"])
        self.assertEqual(sent["headers"]["x-goog-api-key"], "test-key")
        self.assertEqual([c["role"] for c in sent["body"]["contents"]], ["user", "model", "user"])
