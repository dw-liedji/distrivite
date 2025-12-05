from django.urls import include, path
from rest_framework_nested import routers

from apps.api.v1.data import views

app_name = "api"

router = routers.SimpleRouter()
# router.register("users", views.OrganizationUserList, basename="users")

urlpatterns = [
    path("api/v1/auth/", include("apps.api.v1.auth.urls")),
    path("<slug:organization>/api/v1/data/", include("apps.api.v1.data.urls")),
]

urlpatterns += router.urls
