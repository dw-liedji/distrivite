from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path(
        "facturations/",
        views.OrgFacturationGlobalReportView.as_view(),
        name="report",
    ),
    path(
        "facturations/print/",
        views.OrgPrintFacturationGlobalReportView.as_view(),
        name="report_print",
    ),
]
