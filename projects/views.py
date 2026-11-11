from django.shortcuts import get_object_or_404, render

from core.translate import tfield, ui

from .models import Category, Project


def project_list(request):
    projects = Project.objects.filter(is_published=True).prefetch_related("categories")
    cats = Category.objects.filter(projects__is_published=True).distinct()
    return render(request, "projects/list.html", {
        "projects": projects,
        "categories": cats,
        "page_key": "projects",
        "page_title": ui("projects.title"),
    })


def project_detail(request, slug):
    project = get_object_or_404(Project.objects.prefetch_related("images", "categories"), slug=slug, is_published=True)
    published = list(Project.objects.filter(is_published=True).only("slug", "title", "number"))
    i = next((k for k, p in enumerate(published) if p.pk == project.pk), 0)
    nxt = published[(i + 1) % len(published)] if len(published) > 1 else None
    return render(request, "projects/detail.html", {
        "project": project,
        "next_project": nxt,
        "page_key": "project",
        "page_title": project.title,
        "page_description": tfield(project, "summary"),
    })
