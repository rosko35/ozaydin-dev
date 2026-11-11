from django.shortcuts import render


def home(request):
    """Tek sayfalık portfolyo. Sayfalar arası geçiş tarayıcıda (#projeler, #hakkimda...) yapılır."""
    return render(request, "core/index.html")
