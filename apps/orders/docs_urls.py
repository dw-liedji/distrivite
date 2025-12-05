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
        "withdrawals/<str:export_format>/export",
        docs_views.OrgWithdrawalListExportView.as_view(),
        name="withdrawal_list_export",
    ),
    path(
        "batchs/<str:export_format>/export",
        docs_views.OrgBatchListExportView.as_view(),
        name="batch_list_export",
    ),
]
