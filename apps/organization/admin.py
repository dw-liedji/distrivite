from django.contrib import admin
from organizations.models import (
    Organization,
    OrganizationInvitation,
    OrganizationOwner,
    OrganizationUser,
)

from apps.organization import models as org_models

admin.site.unregister(Organization)
admin.site.unregister(OrganizationUser)
admin.site.unregister(OrganizationOwner)
admin.site.unregister(OrganizationInvitation)


class OrganizationUserGroupInline(admin.TabularInline):
    model = org_models.OrganizationUserGroup
    extra = 0


@admin.register(org_models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    pass


@admin.register(org_models.OrganizationUser)
class OrganizationUser(admin.ModelAdmin):
    list_display = ["organization", "user"]
    inlines = [OrganizationUserGroupInline]


@admin.register(org_models.OrganizationOwner)
class OrganizationOwnerAdmin(admin.ModelAdmin):
    pass


@admin.register(org_models.OrganizationGroup)
class OrganizationGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(org_models.OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ["organization", "invitee_identifier", "status"]
