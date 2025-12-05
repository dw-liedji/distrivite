from django.urls import include, path
from organizations.backends import invitation_backend

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
