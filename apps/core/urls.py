from django.urls import path

from . import views

app_name = "core"
from django.views.generic import TemplateView

urlpatterns = [
    # Index: redirect to user organization page
    path("", views.HomePage.as_view(), name="index"),
    # Static page
    path("help/", views.help, name="help"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("subprocessors/", views.subprocessors, name="subprocessors"),
    path("security/", views.security, name="security"),
    path("receipt/", views.receipt, name="receipt"),
    # dal urls for autocompletion
    path(
        "user-autocomplete/",
        views.OrgUserAutocomplete.as_view(),
        name="user-autocomplete",
    ),
    path(
        "customer-autocomplete/",
        views.OrgCustomerAutocomplete.as_view(),
        name="customer-autocomplete",
    ),
    path(
        "category-autocomplete/",
        views.OrgCategoryAutocomplete.as_view(),
        name="category-autocomplete",
    ),
    path(
        "item-autocomplete/",
        views.OrgItemAutocomplete.as_view(),
        name="item-autocomplete",
    ),
    path(
        "batch-autocomplete/",
        views.OrgBatchAutocomplete.as_view(),
        name="batch-autocomplete",
    ),
    path(
        "stock-autocomplete/",
        views.OrgStockAutocomplete.as_view(),
        name="stock-autocomplete",
    ),
]
