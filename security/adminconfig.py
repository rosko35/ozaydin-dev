from django.contrib.admin.apps import AdminConfig


class SecureAdminConfig(AdminConfig):
    """django.contrib.admin yerine kurulur: varsayılan admin sitesi iki adımlı doğrulamalı olur.
    Mevcut tüm @admin.register kayıtları aynen çalışır."""

    default_site = "security.sites.SecureAdminSite"
