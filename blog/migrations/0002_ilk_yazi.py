"""İlk yazı (TASLAK): ozaydin.dev'i nasıl yayına aldım. Emre okuyup admin'den yayına alacak."""
from django.db import migrations

SLUG = "ozaydin-devi-nasil-yayina-aldim"

TAGS = [("sunucu", "sunucu", "server"), ("django", "django", "django")]

BODY_TR = """\
Bu siteyi hazır bir site oluşturucu kullanmadan, Python ve Django ile kendim yazdım. Amacım, bir web sitesinin baştan sona nasıl çalıştığını görmekti.

## Kendi sunucum

Site bir VDS sunucusunda çalışıyor. Kurulumu, güvenliği, HTTPS'i ve gece yedeklerini kendim ayarladım. Bu kısım işin en öğretici tarafı oldu; çoğu adımı ilk denemede değil, bir şeyleri bozup düzelterek öğrendim.

## Tasarım

Sitenin fikri basit: her şey 0 ve 1 ile başlıyor. Arka plandaki 3D alan binlerce 0 ve 1'den oluşuyor ve bulunduğun bölüme göre şekil değiştiriyor. Sayfalar önce metin olarak açılıyor, 3D alan sonra geliyor; böylece site telefonda da hızlı kalıyor.

## Sırada ne var?

Yeni projeler ekleyeceğim ve yaptıklarımı burada kısa notlar hâlinde paylaşacağım.
"""

BODY_EN = """\
I built this site myself with Python and Django instead of using a site builder. I wanted to see how a website works from start to finish.

## My own server

The site runs on a VDS server. I set up the server, its security, HTTPS and nightly backups myself. This turned out to be the most educational part; I learned most steps not on the first try, but by breaking things and fixing them.

## Design

The idea behind the site is simple: everything starts with 0 and 1. The 3D field in the background is made of thousands of 0s and 1s and changes shape depending on the section you're in. Pages load as text first and the 3D field comes after, so the site stays fast on phones too.

## What's next

I'll add new projects and share short notes about what I build here.
"""

POST = {
    "slug": SLUG,
    "title_tr": "ozaydin.dev'i nasıl yayına aldım",
    "title_en": "How I shipped ozaydin.dev",
    "summary_tr": "Bu siteyi Django ile yazıp kendi sunucumda yayına alırken öğrendiklerim.",
    "summary_en": "What I learned while building this site with Django and putting it live on my own server.",
    "body_tr": BODY_TR,
    "body_en": BODY_EN,
    "status": "draft",
}


def seed(apps, schema_editor):
    from blog.markdown import render  # geçmiş modellerde save() yok; HTML'i burada üret

    Tag = apps.get_model("blog", "Tag")
    Post = apps.get_model("blog", "Post")
    Project = apps.get_model("projects", "Project")
    if Post.objects.filter(slug=SLUG).exists():
        return
    tags = [Tag.objects.get_or_create(slug=s, defaults={"name_tr": tr, "name_en": en})[0] for s, tr, en in TAGS]
    post = Post.objects.create(
        **POST,
        body_html_tr=render(BODY_TR),
        body_html_en=render(BODY_EN),
        related_project=Project.objects.filter(slug="ozaydin-dev").first(),
    )
    post.tags.set(tags)


def unseed(apps, schema_editor):
    apps.get_model("blog", "Post").objects.filter(slug=SLUG).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0001_initial"),
        ("projects", "0002_seed"),
    ]
    operations = [migrations.RunPython(seed, unseed)]
