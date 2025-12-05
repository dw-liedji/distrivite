from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("pricing/", view=views.pricing, name="pricing"),
]
