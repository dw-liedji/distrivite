from django.urls import include, path
from rest_framework_nested import routers

from apps.api.v1.data import views

app_name = "data_v1"

router = routers.SimpleRouter()
# router.register("users", views.OrganizationUserList, basename="users")

urlpatterns = [
    path(
        "sales/",
        views.FacturationListView.as_view(),
        name="sale-list",
    ),
    path(
        "sale-ids/",
        views.FacturationIdListsView.as_view(),
        name="sale-id-list",
    ),
    path(
        "sale-changes/",
        views.FacturationChangesView.as_view(),
        name="sale-changes",
    ),
    path(
        "sales/create/",
        views.FacturationCreateView.as_view(),
        name="sale-create",
    ),
    path(
        "sales/<uuid:pk>/",
        views.FacturationRetrieveView.as_view(),
        name="sale-detail",
    ),
    path(
        "sales/<uuid:pk>/edit/",
        views.FacturationUpdateView.as_view(),
        name="sale-update",
    ),
    path(
        "sales/<uuid:pk>/delete/",
        views.FacturationDeleteView.as_view(),
        name="sale-delete",
    ),
    path("transactions/", views.TransactionListAPIView.as_view()),
    path(
        "transactions/create/",
        views.TransactionCreateView.as_view(),
        name="transaction-create",
    ),
    path("customers/", views.CustomerListAPIView.as_view(), name="customer-list"),
    path(
        "customers/create/",
        views.CustomerCreateView.as_view(),
        name="customer-create",
    ),
    path("stocks/", views.BatchListAPIView.as_view()),
    path("users/", views.OrganizationUserList.as_view()),
    path("make-payment/", views.make_payment, name="make-payment"),
]

urlpatterns += router.urls
