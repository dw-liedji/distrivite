from django.contrib import admin

from . import models


@admin.register(models.Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]


class PlanFeatureInline(admin.TabularInline):
    model = models.PlanFeature
    extra = 1


@admin.register(models.Plan)
class PlanAdmin(admin.ModelAdmin):
    inlines = [PlanFeatureInline]


@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "plan",
        "paid_status",
        "created",
        "modified",
    )
