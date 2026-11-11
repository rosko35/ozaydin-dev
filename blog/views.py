"""Blog görünümleri: liste, etiket, yazı, RSS."""
from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.feedgenerator import Rss201rev2Feed

from core.translate import lang, tfield, ui

from .models import Post, Tag

PER_PAGE = 10


def _list(request, posts, extra):
    page = Paginator(posts, PER_PAGE).get_page(request.GET.get("page") or request.GET.get("sayfa"))
    tags = Tag.objects.filter(posts__in=Post.objects.published()).distinct()
    return render(request, "blog/list.html", {
        "page_obj": page,
        "posts": page.object_list,
        "total": page.paginator.count,
        "tags": tags,
        "page_key": "blog",
        **extra,
    })


def post_list(request):
    posts = Post.objects.published().prefetch_related("tags")
    return _list(request, posts, {"page_title": ui("blog.title"), "page_description": ui("blog.description")})


def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.published().filter(tags=tag).prefetch_related("tags")
    name = tfield(tag, "name")
    return _list(request, posts, {
        "tag": tag,
        "page_title": f"#{name} · {ui('blog.title')}",
        "page_description": ui("blog.tag_description", tag=name),
    })


def _wants_preview(request):
    return request.user.is_authenticated and request.user.is_staff and (
        request.GET.get("onizleme") == "1" or request.GET.get("preview") == "1"
    )


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related("related_project").prefetch_related("tags"), slug=slug)
    preview = not post.is_published
    if preview and not _wants_preview(request):
        raise Http404

    order = list(Post.objects.published().order_by("published_at", "id").values_list("id", flat=True))
    pos = {pk: i + 1 for i, pk in enumerate(order)}  # 1'den başlayan sıra (eskiden yeniye)
    prev_post = next_post = None
    if not preview:
        i = order.index(post.pk)
        ids = {"prev": order[i - 1] if i > 0 else None, "next": order[i + 1] if i + 1 < len(order) else None}
        found = {p.pk: p for p in Post.objects.filter(pk__in=[v for v in ids.values() if v]).only("slug", "title_tr", "title_en")}
        prev_post, next_post = found.get(ids["prev"]), found.get(ids["next"])
        for p in (prev_post, next_post):
            if p:
                p.idx = format(pos[p.pk], "b")

    return render(request, "blog/post.html", {
        "post": post,
        "article": post,
        "preview": preview,
        "idx": format(pos[post.pk], "b") if post.pk in pos else "0",
        "prev_post": prev_post,
        "next_post": next_post,
        "og_image": request.build_absolute_uri(post.cover.url) if post.cover else None,
        "page_key": "post",
        "page_title": tfield(post, "title"),
        "page_description": tfield(post, "summary"),
    })


def lreverse(name, **kw):
    # core.routes bu modülü içe aktarıyor; döngü olmasın diye burada, çağrı anında.
    from core.routes import lreverse as _lreverse
    return _lreverse(name, **kw)


class PostFeed(Feed):
    """RSS 2.0. Dil adresten gelir: /blog/rss/ Türkçe, /en/blog/rss/ İngilizce."""

    feed_type = Rss201rev2Feed

    def title(self):
        return ui("blog.rss_title")

    def link(self):
        return lreverse("blog")

    def description(self):
        return ui("blog.description")

    def feed_url(self):
        return lreverse("blog_feed")

    # language: boş bırakıldı; Feed, etkin dili (adresten seçilen) kullanır.

    def items(self):
        return Post.objects.published().prefetch_related("tags")[:20]

    def item_title(self, item):
        return tfield(item, "title")

    def item_description(self, item):
        text = tfield(item, "summary")
        if item.only_tr:
            text = f"{text} ({ui('blog.only_tr')})"
        return text

    def item_link(self, item):
        return item.get_absolute_url(lang())

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated

    def item_categories(self, item):
        return [tfield(t, "name") for t in item.tags.all()]

    def item_author_name(self, item):
        return "Emre Özaydın"


feed = PostFeed()
