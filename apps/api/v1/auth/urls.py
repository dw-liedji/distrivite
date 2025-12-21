from django.urls import include, path

from apps.api.v1.auth import views

app_name = "auth_v1"

urlpatterns = [
    path("", include("djoser.urls")),
    path("", include("djoser.urls.jwt")),
    path("org/verify/", views.verify_org, name="verify_org"),
    path("org/verify2/", views.verify_org2, name="verify_org"),
]
