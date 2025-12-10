from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views as organization_views

app_name = "organization_features"

urlpatterns = [
    path(
        "things/",
        include("apps.organization.org_things", namespace="org_things"),
    ),
    path(
        "reports/",
        include("apps.reports.org_urls", namespace="org_reports"),
    ),
    path(
        "orders/",
        include("apps.orders.urls", namespace="orders"),
    ),
    path(
        "order_docs/",
        include("apps.orders.docs_urls", namespace="order_docs"),
    ),
    # path(
    #     "cashflow/",
    #     include("apps.cashflow.urls", namespace="cashflow"),
    # ),
    # path(
    #     "coverages/",
    #     include("apps.coverages.urls", namespace="coverages"),
    # ),
    # path(
    #     "api/",
    #     include("apps.api.docta.urls", namespace="api"),
    # ),
]
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
