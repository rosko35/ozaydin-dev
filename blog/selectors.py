from .models import Post


def latest_posts(limit=3):
    """Ana sayfadaki 'Yazılar' bölümü için son yayımlanan yazılar."""
    return list(Post.objects.published().prefetch_related("tags")[:limit])
