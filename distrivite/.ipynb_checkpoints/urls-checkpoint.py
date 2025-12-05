from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "distrivite Space"
admin.site.index_title = "distrivite Space"
admin.site.site_title = "distrivite Space"
from django.conf.urls.i18n import i18n_patterns

from .views import language_redirect

urlpatterns = [
    # This is for fixing heroku home page language 404
    path("", language_redirect),
    path("__debug__/", include("debug_toolbar.urls")),
    path("qr_code/", include("qr_code.urls", namespace="qr_code")),
]

urlpatterns += i18n_patterns(
    # Users urls
    path("", include("apps.core.urls")),
    path("users/", include("apps.users.urls")),
    path("subscriptions/", include("apps.subscriptions.urls")),
    # iot for internet of things urls
    # path("iot/", include("apps.iot.urls")),
    # # Admin
    path("admin/", admin.site.urls),
    # Rosetta’s URLs
    path("rosetta/", include("rosetta.urls")),
    # Organizations urls
    path("organizations/", include("apps.organization.urls")),
    # Organizations features urls
    path(
        "<slug:organization>/",
        include("apps.organization.features_urls"),
        name="organization_features",
    ),
    # path("reports/", include("apps.reports.urls")),
    prefix_default_language=True,
)

urlpatterns = (
    urlpatterns
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)


# Error pages
handler400 = "apps.core.views.handle_400"
handler403 = "apps.core.views.handle_403"
handler404 = "apps.core.views.handle_404"
handler500 = "apps.core.views.handle_500"
