from django.contrib import admin
from organizations.models import (
    Organization,
    OrganizationInvitation,
    OrganizationOwner,
    OrganizationUser,
)

admin.site.unregister(Organization)
admin.site.unregister(OrganizationUser)
admin.site.unregister(OrganizationOwner)
admin.site.unregister(OrganizationInvitation)

from apps.organization.models import (
    Organization,
    OrganizationGroup,
    OrganizationInvitation,
    OrganizationOwner,
    OrganizationUser,
    OrganizationUserGroup,
)


class OrganizationUserGroupInline(admin.TabularInline):
    model = OrganizationUserGroup
    extra = 0


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    pass


@admin.register(OrganizationUser)
class OrganizationUser(admin.ModelAdmin):
    list_display = ["organization", "user"]
    inlines = [OrganizationUserGroupInline]


@admin.register(OrganizationOwner)
class OrganizationOwnerAdmin(admin.ModelAdmin):
    pass


@admin.register(OrganizationGroup)
class OrganizationGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ["organization", "invitee_identifier", "status"]
