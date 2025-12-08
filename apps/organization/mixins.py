from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

# views.py
from rest_framework.views import APIView

from apps.organization.models import Organization, OrganizationUser


class OrganizationAPIUserMixin:
    """Mixin for DRF views to set organization_user"""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        # Now authentication is complete

        if hasattr(request, "organization"):

            if request.user and request.user.is_authenticated:
                organization_user = OrganizationUser.objects.filter(
                    organization=request.organization, user=request.user
                ).first()

                if organization_user:
                    request.organization_user = organization_user
                else:
                    # Handle unauthorized access to organization
                    pass


class OrgPermissionRequiredMixin(PermissionRequiredMixin):
    """This base mixin presumes that authentication has already been checked"""

    def has_permission(self):
        """
        Override this method to customize the way permissions are checked.
        """
        perms = self.get_permission_required()
        organization_user = self.request.organization_user
        return organization_user.has_perms(perms) or organization_user.is_admin


class DatavitePermissionsMixin(object):
    """This base mixin presumes that authentication has already been checked"""

    permission_denied_message = "Permission denied"

    def has_permissions(self):
        return True

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permissions():
            raise PermissionDenied(self.permission_denied_message)
        return super(DatavitePermissionsMixin, self).dispatch(request, *args, **kwargs)


class OrgFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.organization
        kwargs["organization_user"] = self.request.organization_user
        return kwargs


class OrgOnlyFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.organization
        kwargs["user"] = self.request.user
        return kwargs


class OrgUserOnlyFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization_user"] = self.request.organization_user
        return kwargs


class UserFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MembershipRequiredMixin(DatavitePermissionsMixin):
    """This mixin presumes that authentication has already been checked"""

    permission_denied_message = "Membership required to access this page."

    def has_permissions(self):
        return (
            self.request.organization.is_member(self.request.user)
            and self.request.organization_user.is_active
        )


class AdminRequiredMixin:
    """This mixin presumes that authentication has already been checked"""

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        if (
            not self.request.organization.is_admin(request.user)
            and not request.user.is_superuser
        ):
            raise PermissionDenied(_("Sorry, admins only"))
        return super().dispatch(request, *args, **kwargs)


class OwnerRequiredMixin:
    """This mixin presumes that authentication has already been checked"""

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        if (
            self.request.organization.owner.organization_user.user != request.user
            and not request.user.is_superuser
        ):
            raise PermissionDenied(_("You are not the organization owner"))
        return super().dispatch(request, *args, **kwargs)


class ActiveSubscriptionRequiredMixin:
    """This mixin presumes that authentication has already been checked"""

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

        subscription = request.organization.current_subscription

        if not request.user.is_superuser:
            if subscription is None:
                raise PermissionDenied(
                    _(
                        "You don't have a subscription consider checking for bill payments."
                    )
                )
            elif not subscription.is_active:
                raise PermissionDenied(
                    _(
                        "You current subscription has expired, please consider checking for bill payments."
                    )
                )
        return super().dispatch(request, *args, **kwargs)
