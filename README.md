# ozaydin.dev

Personal portfolio site of Emre Özaydın. Live at <https://ozaydin.dev>.

A bilingual (Turkish / English) portfolio and blog written in Django and run on my own Ubuntu server. The pages sit on a Three.js 3D field made of 0s and 1s that changes shape as you scroll and move between pages.

## Features

- Turkish at the root, English under `/en/`, with matching addresses for every page.
- Projects managed from the admin panel: photo gallery, demo video, and uploaded images are resized and converted to WebP automatically.
- Markdown blog with tags, an RSS feed, and draft preview.
- Working contact form with spam protection (hidden field, rate limit, link check) and e-mail notification.
- Chat assistant powered by Gemini, with request limits.
- SEO: sitemap, hreflang, Open Graph cards generated automatically, JSON-LD.
- pjax page transitions.
- Nightly backup of the database and uploaded files.

## Stack

Python 3.14, Django 6.1, PostgreSQL, Gunicorn, Nginx, Let's Encrypt, Three.js r128, Ubuntu 24.04 VDS. Locally it uses SQLite.

## Layout

```
config/    settings, URL configuration, WSGI/ASGI
core/      base template, routes, translations, SEO, Open Graph cards, static files (CSS, JS, fonts, Three.js)
projects/  projects, categories, gallery images, demo videos
blog/      posts, tags, Markdown rendering, RSS
contact/   contact form and message storage
chat/      chat assistant
deploy/    server files: deploy script, Nginx, systemd units, backup
```

## Running locally

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Nothing needs to be configured for local development. The site is then at <http://127.0.0.1:8000>. Use `python manage.py createsuperuser` to log in to the admin panel.

### Environment variables

Only needed on the server. Defaults are for local development.

| Variable | Purpose | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Secret key; set a long random value in production | insecure dev key |
| `DJANGO_DEBUG` | `1` for development, `0` in production | `1` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names | `127.0.0.1,localhost` |
| `DJANGO_DB_NAME` | PostgreSQL database name; if unset, SQLite is used | unset |
| `DJANGO_ADMIN_URL` | Admin panel path | `admin/` |
| `DJANGO_SITE_URL` | Public site address (used in sitemap, cards, feeds) | `https://ozaydin.dev` |
| `DJANGO_EMAIL_HOST` / `DJANGO_EMAIL_PORT` | SMTP server | `smtp.gmail.com` / `587` |
| `DJANGO_EMAIL_HOST_USER` / `DJANGO_EMAIL_HOST_PASSWORD` | SMTP account; if unset, e-mails are printed to the console | unset |
| `DJANGO_CONTACT_TO` | Address that receives contact form messages | set in `settings.py` |
| `DJANGO_CHAT_PROVIDER` | Chat provider | `gemini` |
| `DJANGO_CHAT_API_KEY` | Chat provider key; if unset, the chat button is hidden | unset |
| `DJANGO_CHAT_MODEL` | Chat model name | `gemini-flash-lite-latest` |

## Deployment

The `deploy/` folder holds everything the server needs:

- `deploy.sh`: pulls the latest code, installs packages, migrates, collects static files, restarts the service.
- `nginx-ozaydin-dev.conf`, `nginx-ozaydin-dev.https.conf`: Nginx configuration (HTTP first, then HTTPS).
- `ozaydin-dev.service`: systemd unit that runs Gunicorn.
- `backup.sh`, `ozaydin-backup.service`, `ozaydin-backup.timer`: nightly backup; `restore.md` explains how to restore.

The latest set of server steps is in [`deploy/GUNCELLEME-12-KASIM.md`](deploy/GUNCELLEME-12-KASIM.md) (written in Turkish).

## Tests

```bash
python manage.py test
```

## Contact

Use the [contact page](https://ozaydin.dev/en/contact/) or [LinkedIn](https://www.linkedin.com/in/emre-%C3%B6zayd%C4%B1n-b65409270/).

## License

The code is All rights reserved. The Geist fonts are under the SIL Open Font License ([`core/static/core/fonts/OFL-geist.txt`](core/static/core/fonts/OFL-geist.txt)) and three.js is under the MIT license ([`core/static/core/vendor/three-LICENSE.txt`](core/static/core/vendor/three-LICENSE.txt)); both keep their own licenses.

---

# Türkçe

Emre Özaydın'ın kişisel portfolyo sitesi. Canlı adres: <https://ozaydin.dev>.

Django ile yazılmış, kendi Ubuntu sunucumda çalışan iki dilli (Türkçe / İngilizce) bir portfolyo ve blog. Sayfaların arkasında 0 ve 1'lerden oluşan bir Three.js 3D alanı var; kaydırdıkça ve sayfalar arasında gezdikçe şekil değiştiriyor.

## Özellikler

- Türkçe kök adreste, İngilizce `/en/` altında; her sayfanın iki dilde karşılığı var.
- Admin panelinden yönetilen projeler: fotoğraf galerisi, demo videosu, yüklenen görseller otomatik küçültülüp WebP'ye çevrilir.
- Markdown blog: etiketler, RSS, taslak önizleme.
- Çalışan iletişim formu: spam koruması (gizli alan, hız sınırı, link denetimi) ve e-posta bildirimi.
- Gemini ile çalışan sohbet asistanı, istek sınırlarıyla.
- SEO: sitemap, hreflang, otomatik üretilen Open Graph kartları, JSON-LD.
- pjax sayfa geçişleri.
- Veritabanı ve yüklenen dosyaların gece yedeği.

## Teknoloji yığını

Python 3.14, Django 6.1, PostgreSQL, Gunicorn, Nginx, Let's Encrypt, Three.js r128, Ubuntu 24.04 VDS. Yerelde SQLite kullanılır.

## Klasör yapısı

```
config/    ayarlar, adres yapılandırması, WSGI/ASGI
core/      ana şablon, adresler, çeviriler, SEO, Open Graph kartları, statik dosyalar (CSS, JS, yazı tipleri, Three.js)
projects/  projeler, kategoriler, galeri görselleri, demo videoları
blog/      yazılar, etiketler, Markdown dönüştürme, RSS
contact/   iletişim formu ve mesaj kayıtları
chat/      sohbet asistanı
deploy/    sunucu dosyaları: yayına alma betiği, Nginx, systemd servisleri, yedek
```

## Yerelde çalıştırma

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Yerelde hiçbir şey ayarlamak gerekmez. Site <http://127.0.0.1:8000> adresinde açılır. Admin paneline girmek için `python manage.py createsuperuser` çalıştır.

### Ortam değişkenleri

Sadece sunucuda gerekir. Varsayılanlar yerel geliştirme içindir.

| Değişken | Ne işe yarar | Varsayılan |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Gizli anahtar; yayında uzun, rastgele bir değer ver | güvensiz geliştirme anahtarı |
| `DJANGO_DEBUG` | Geliştirmede `1`, yayında `0` | `1` |
| `DJANGO_ALLOWED_HOSTS` | Virgülle ayrılmış alan adları | `127.0.0.1,localhost` |
| `DJANGO_DB_NAME` | PostgreSQL veritabanı adı; yoksa SQLite kullanılır | boş |
| `DJANGO_ADMIN_URL` | Admin paneli adresi | `admin/` |
| `DJANGO_SITE_URL` | Sitenin herkese açık adresi (sitemap, kartlar, RSS için) | `https://ozaydin.dev` |
| `DJANGO_EMAIL_HOST` / `DJANGO_EMAIL_PORT` | SMTP sunucusu | `smtp.gmail.com` / `587` |
| `DJANGO_EMAIL_HOST_USER` / `DJANGO_EMAIL_HOST_PASSWORD` | SMTP hesabı; yoksa e-postalar konsola yazılır | boş |
| `DJANGO_CONTACT_TO` | İletişim formu mesajlarının gideceği adres | `settings.py` içinde |
| `DJANGO_CHAT_PROVIDER` | Sohbet sağlayıcısı | `gemini` |
| `DJANGO_CHAT_API_KEY` | Sohbet sağlayıcısının anahtarı; yoksa sohbet düğmesi görünmez | boş |
| `DJANGO_CHAT_MODEL` | Sohbet modelinin adı | `gemini-flash-lite-latest` |

## Yayına alma

`deploy/` klasöründe sunucunun ihtiyacı olan her şey var:

- `deploy.sh`: son kodu çeker, paketleri kurar, veritabanını günceller, statik dosyaları toplar, servisi yeniden başlatır.
- `nginx-ozaydin-dev.conf`, `nginx-ozaydin-dev.https.conf`: Nginx ayarı (önce HTTP, sonra HTTPS).
- `ozaydin-dev.service`: Gunicorn'u çalıştıran systemd servisi.
- `backup.sh`, `ozaydin-backup.service`, `ozaydin-backup.timer`: gece yedeği; geri dönmek için `restore.md`.

Sunucuda yapılacak son adımlar [`deploy/GUNCELLEME-12-KASIM.md`](deploy/GUNCELLEME-12-KASIM.md) dosyasında.

## Testler

```bash
python manage.py test
```

## İletişim

[İletişim sayfası](https://ozaydin.dev/iletisim/) ya da [LinkedIn](https://www.linkedin.com/in/emre-%C3%B6zayd%C4%B1n-b65409270/).

## Lisans

Kodun tüm hakları saklıdır. Geist yazı tipleri SIL Open Font License ([`core/static/core/fonts/OFL-geist.txt`](core/static/core/fonts/OFL-geist.txt)), three.js MIT lisansı ([`core/static/core/vendor/three-LICENSE.txt`](core/static/core/vendor/three-LICENSE.txt)) altındadır; ikisi de kendi lisanslarını korur.
