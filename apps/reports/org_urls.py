from django.urls import path

from . import views

app_name = "org_reports"

urlpatterns = [
    path(
        "report/",
        views.OrgReportView.as_view(),
        name="report",
    ),
    path(
        "report/print/",
        views.OrgReportPrintView.as_view(),
        name="report_print",
    ),
]
