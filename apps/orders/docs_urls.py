from django.urls import path

from . import docs_views

app_name = "order_docs"

urlpatterns = [
    path(
        "facturations/<str:export_format>/export",
        docs_views.OrgFacturationListExportView.as_view(),
        name="facturation_list_export",
    ),
    path(
        "transactions/<str:export_format>/export",
        docs_views.OrgTransactionListExportView.as_view(),
        name="transaction_list_export",
    ),
    path(
        "batchs/<str:export_format>/export",
        docs_views.OrgBatchListExportView.as_view(),
        name="batch_list_export",
    ),
    path(
        "stocks/<str:export_format>/export",
        docs_views.OrgStockListExportView.as_view(),
        name="stock_list_export",
    ),
]
