from django.utils import translation


class LanguageFromPath:
    """/en/ ile başlayan adresler İngilizce, diğerleri Türkçe. Tarayıcı diline bakılmaz; adres belirler."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = "en" if request.path_info == "/en" or request.path_info.startswith("/en/") else "tr"
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        response.headers.setdefault("Content-Language", lang)
        return response
