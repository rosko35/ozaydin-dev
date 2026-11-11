"""Blog görünümleri. (Geçici iskelet: blog adımında doldurulacak.)"""
from django.http import Http404
from django.shortcuts import render

from core.translate import ui


def post_list(request):
    return render(request, "blog/list.html", {"page_key": "blog", "page_title": ui("blog.title"), "posts": []})


def post_detail(request, slug):
    raise Http404


def tag_detail(request, slug):
    raise Http404


def feed(request):
    raise Http404
