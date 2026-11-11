from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.routes import urlpatterns_for

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("core.urls")),  # dilden bağımsız: robots.txt, sitemap.xml
    path("en/", include((urlpatterns_for("en"), "en"), namespace="en")),
    path("", include((urlpatterns_for("tr"), "tr"), namespace="tr")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "ozaydin.dev yönetim"
admin.site.site_title = "ozaydin.dev"
admin.site.index_title = "İçerik"
handler404 = 'core.views.not_found'
