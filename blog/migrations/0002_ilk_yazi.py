"""İlk yazı (TASLAK): ozaydin.dev'i nasıl yayına aldım. Emre okuyup admin'den yayına alacak."""
from django.db import migrations

SLUG = "ozaydin-devi-nasil-yayina-aldim"

TAGS = [("sunucu", "sunucu", "server"), ("django", "django", "django")]

BODY_TR = """\
Bu site, kiraladığım küçük bir sunucuda çalışıyor. Hazır bir barındırma paneli yerine her parçayı kendim kurmak istedim: hem neyin nerede durduğunu öğrenmek için hem de ileride bir şey bozulursa nereye bakacağımı bilmek için. Bu yazı o kurulumun kısa bir özeti.

## Sunucu

DeHost'tan 2 GB RAM'li bir VDS aldım, işletim sistemi olarak Ubuntu 24.04 seçtim. İlk iş güvenlik oldu: kendime `emre` adında bir kullanıcı açtım, bilgisayarımdaki SSH anahtarını ekledim, sonra root girişini ve şifreyle girişi kapattım. Artık sunucuya sadece anahtarla girilebiliyor.

Güvenlik duvarı için UFW kullandım. Dışarıya açık üç şey var: SSH, 80 ve 443.

## Python, veritabanı, uygulama

Ubuntu 24.04, Python 3.12 ile geliyor; ben bilgisayarımda 3.14 kullanıyorum. İki ortam aynı olsun diye sunucuda Python 3.14'ü `uv` ile kurdum, sanal ortamı da onunla oluşturdum.

Veritabanı PostgreSQL. Şifre kullanmıyorum: Django, Linux kullanıcısıyla aynı adlı PostgreSQL kullanıcısı olarak yerel soket üzerinden bağlanıyor (peer authentication). Böylece ayar dosyalarında saklanması gereken bir veritabanı şifresi de yok.

Django'yu Gunicorn çalıştırıyor. Onu bir systemd servisi yaptım; sunucu yeniden başlarsa site de kendiliğinden açılıyor. Servis dosyasının önemli kısmı şu:

```ini
[Service]
User=emre
Group=www-data
WorkingDirectory=/srv/ozaydin-dev
EnvironmentFile=/etc/ozaydin-dev.env
ExecStart=/srv/ozaydin-dev/.venv/bin/gunicorn config.wsgi:application \\
    --workers 3 \\
    --bind unix:/run/ozaydin-dev/gunicorn.sock
Restart=on-failure
```

Gizli ayarlar (`SECRET_KEY` gibi) depoda değil, sunucudaki `/etc/ozaydin-dev.env` dosyasında duruyor. Önde Nginx var: statik dosyaları kendisi veriyor, geri kalan istekleri bu soket üzerinden Gunicorn'a iletiyor.

## Alan adı ve HTTPS

Alan adım Hostinger'da. DNS panelinden `@` için sunucunun IP adresine bir A kaydı, `www` için de bir CNAME kaydı ekledim.

Burada bilmem gereken bir ayrıntı vardı: `.dev` alan adları tarayıcılarda HSTS listesine baştan ekli, yani sadece HTTPS ile açılıyorlar. Sertifika olmadan site tarayıcıda hiç görünmüyor. Bu yüzden sıra önemli: önce DNS, sonra Nginx, hemen ardından sertifika. Sertifikayı Let's Encrypt'ten Certbot ile aldım:

```bash
sudo certbot --nginx -d ozaydin.dev -d www.ozaydin.dev
```

Certbot, Nginx ayarına HTTPS satırlarını kendisi ekliyor ve sertifikayı süresi dolmadan otomatik olarak yeniliyor.

## Sonrası

Güncellemeler için küçük bir `deploy.sh` yazdım: kodu GitHub'dan çekiyor, paketleri kuruyor, `migrate` ve `collectstatic` çalıştırıyor, servisi yeniden başlatıyor. Sıradaki iş her gece veritabanı yedeği almak ve bu yedeğin bir kopyasını sunucunun dışında tutmak.
"""

BODY_EN = """\
This site runs on a small server I rent. Instead of a ready-made hosting panel, I wanted to set up every piece myself: partly to learn where everything lives, partly so I know where to look if something breaks later. This post is a short summary of that setup.

## The server

I got a VDS with 2 GB of RAM from DeHost and chose Ubuntu 24.04. Security came first: I created a user called `emre`, added the SSH key from my computer, then turned off root login and password login. The server now only accepts key-based logins.

For the firewall I used UFW. Only three things are open: SSH, 80 and 443.

## Python, database, app

Ubuntu 24.04 ships with Python 3.12, while I use 3.14 on my computer. To keep both environments the same, I installed Python 3.14 on the server with `uv` and created the virtual environment with it.

The database is PostgreSQL. There is no password: Django connects over the local socket as the PostgreSQL user with the same name as the Linux user (peer authentication). So there is no database password to keep in a config file either.

Gunicorn runs Django. I made it a systemd service, so if the server restarts, the site comes back up by itself. The important part of the service file:

```ini
[Service]
User=emre
Group=www-data
WorkingDirectory=/srv/ozaydin-dev
EnvironmentFile=/etc/ozaydin-dev.env
ExecStart=/srv/ozaydin-dev/.venv/bin/gunicorn config.wsgi:application \\
    --workers 3 \\
    --bind unix:/run/ozaydin-dev/gunicorn.sock
Restart=on-failure
```

Secrets (like `SECRET_KEY`) are not in the repository; they live in `/etc/ozaydin-dev.env` on the server. Nginx sits in front: it serves static files itself and passes everything else to Gunicorn through that socket.

## Domain and HTTPS

My domain is registered with Hostinger. In the DNS panel I added an A record for `@` pointing to the server's IP address and a CNAME record for `www`.

There was one detail I needed to know: `.dev` domains are on the browsers' HSTS preload list, so they only open over HTTPS. Without a certificate the site doesn't show up in the browser at all. That makes the order important: DNS first, then Nginx, then the certificate right away. I got the certificate from Let's Encrypt with Certbot:

```bash
sudo certbot --nginx -d ozaydin.dev -d www.ozaydin.dev
```

Certbot adds the HTTPS lines to the Nginx config itself and renews the certificate automatically before it expires.

## What's next

For updates I wrote a small `deploy.sh`: it pulls the code from GitHub, installs packages, runs `migrate` and `collectstatic`, and restarts the service. Next on the list is a nightly database backup, with a copy kept off the server.
"""

POST = {
    "slug": SLUG,
    "title_tr": "ozaydin.dev'i nasıl yayına aldım",
    "title_en": "How I shipped ozaydin.dev",
    "summary_tr": "Kiraladığım küçük bir sunucuda bu siteyi nasıl yayına aldığımın kısa özeti: SSH, UFW, PostgreSQL, Gunicorn, Nginx ve HTTPS.",
    "summary_en": "A short summary of how I put this site live on a small rented server: SSH, UFW, PostgreSQL, Gunicorn, Nginx and HTTPS.",
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
