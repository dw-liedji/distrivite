from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "app_label", "model")


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("id", "content_type", "name", "codename")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "email",
        "is_patient",
    ]
    ordering = ("username",)
    search_fields = (
        "username",
        "email",
    )
    list_per_page = 50
