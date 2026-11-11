"""İletişim sayfası. (Geçici iskelet: form gönderimi iletişim adımında yazılacak.)"""
from django.http import JsonResponse
from django.shortcuts import render

from core.translate import ui


def contact(request):
    if request.method == "POST":
        return JsonResponse({"ok": False, "message": "Henüz hazır değil."}, status=501)
    return render(request, "contact/contact.html", {"page_key": "contact", "page_title": ui("contact.title")})
