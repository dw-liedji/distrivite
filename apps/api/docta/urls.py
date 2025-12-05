from django.urls import include, path

from . import views

app_name = "api"

urlpatterns = [
    path("reports/sale/", views.OrgSaleReportAPI.as_view(), name="sales-report"),
    path(
        "reports/cashflow/", views.CashflowReportAPI.as_view(), name="cashflow-report"
    ),
]

# print(urlpatterns)
