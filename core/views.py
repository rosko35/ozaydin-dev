from django.shortcuts import render

from blog.selectors import latest_posts
from core.translate import ui
from projects.models import Project


def home(request):
    projects = Project.objects.filter(is_published=True)
    featured = projects.filter(featured=True) or projects
    return render(request, "core/home.html", {
        "projects": featured[:6],
        "posts": latest_posts(3),
        "page_key": "home",
    })


def about(request):
    return render(request, "core/about.html", {"page_key": "about", "page_title": ui("about.title")})


def not_found(request, exception=None):
    return render(request, "404.html", {"page_key": "404", "page_title": ui("404.title")}, status=404)
