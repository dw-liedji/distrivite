from django.contrib import admin

from . import models

# @admin.register(models.CoverageFacturation)
# class CoverageFacturationAdmin(admin.ModelAdmin):
#     list_display = ["patient"]


# @admin.register(models.MedicalVisit)
# class MedicalVisitAdmin(admin.ModelAdmin):
#     list_display = ["patient"]


@admin.register(models.Facturation)
class FacturationAdmin(admin.ModelAdmin):
    list_display = ["customer"]
