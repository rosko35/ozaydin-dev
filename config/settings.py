"""
ozaydin.dev ayarları.

Bilgisayarında hiçbir şey ayarlamadan çalışır (geliştirme modu).
Sunucuda şu ortam değişkenleri ayarlanır:
  DJANGO_SECRET_KEY      uzun, rastgele bir anahtar
  DJANGO_DEBUG           0
  DJANGO_ALLOWED_HOSTS   ozaydin.dev,www.ozaydin.dev
  DJANGO_DB_NAME         ozaydin (PostgreSQL veritabanı adı)
  DJANGO_ADMIN_URL       yönetim paneli adresi (varsayılan: admin/)
  DJANGO_EMAIL_HOST_USER / DJANGO_EMAIL_HOST_PASSWORD   iletişim formu bildirimi (Gmail uygulama şifresi)
  DJANGO_CONTACT_TO      mesajların gideceği adres
  DJANGO_CHAT_PROVIDER / DJANGO_CHAT_API_KEY / DJANGO_CHAT_MODEL   sohbet asistanı (gemini ya da anthropic)
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
CSRF_TRUSTED_ORIGINS = ["https://ozaydin.dev", "https://www.ozaydin.dev"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "core",
    "projects",
    "blog",
    "contact",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core.middleware.LanguageFromPath",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Bilgisayarda SQLite. Sunucuda DJANGO_DB_NAME ayarlıysa PostgreSQL kullanılır.
# Sunucuda şifre yok: Django, Linux kullanıcısıyla aynı adlı PostgreSQL kullanıcısı olarak
# yerel soket üzerinden bağlanır (peer authentication).
if os.environ.get("DJANGO_DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["DJANGO_DB_NAME"],
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "tr"
LANGUAGES = [("tr", "Türkçe"), ("en", "English")]
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Admin'den yüklenen dosyalar (proje fotoğrafları, blog kapakları). Sunucuda Nginx /media/ altından verir.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Yayında statik dosyaların adına içerik özeti eklenir (site.3f2a1c.css): tarayıcı uzun süre önbellekte tutar,
# dosya değişince adı da değişir. Bilgisayarda (DEBUG) gerek yok.
if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
    }
SITE_URL = os.environ.get("DJANGO_SITE_URL", "https://ozaydin.dev")
ADMIN_URL = os.environ.get("DJANGO_ADMIN_URL", "admin/")

# E-posta: ayarlı değilse mesajlar sadece admin'e kaydedilir, e-posta gönderilmez.
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or "noreply@ozaydin.dev"
# Sitedeki sohbet asistanı. Anahtar yoksa düğme hiç görünmez.
CHAT_PROVIDER = os.environ.get("DJANGO_CHAT_PROVIDER", "gemini")
CHAT_API_KEY = os.environ.get("DJANGO_CHAT_API_KEY", "")
CHAT_MODEL = os.environ.get("DJANGO_CHAT_MODEL", "gemini-flash-lite-latest")
CONTACT_TO = os.environ.get("DJANGO_CONTACT_TO", "emreozaydn60@gmail.com")
if not EMAIL_HOST_USER:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Yayında (DEBUG kapalıyken) güvenlik ayarları
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
