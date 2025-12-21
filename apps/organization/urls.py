from django.urls import path

from apps.organization import views

from . import views

app_name = "organizations"

urlpatterns = [
    path(
        "create/",
        views.organization_create,
        name="organization_create",
    )
]
