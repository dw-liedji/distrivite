from functools import cached_property

from django.contrib.auth.models import Permission
from django.db import models
from django.utils.itercompat import is_iterable
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, MPTTModelBase, TreeForeignKey
from organizations.abstract import (
    AbstractOrganization,
    AbstractOrganizationInvitation,
    AbstractOrganizationOwner,
    AbstractOrganizationUser,
    OrgMeta,
)
from timezone_field import TimeZoneField

from apps.core.models import BaseModel
from apps.organization.managers import (
    OrgFeatureManager,
    OrgManager,
    OrgOwnerManager,
    OrgUserManager,
)


class CommonMeta(MPTTModelBase, OrgMeta, BaseModel.Meta):
    pass


class Organization(MPTTModel, AbstractOrganization, BaseModel, metaclass=CommonMeta):

    class TypeChoices(models.TextChoices):
        NORMAL = "NOR", "NORMAL"
        AFFILIATED = "AFF", "AFFILIATED"

    class BillingTemplateChoices(models.TextChoices):
        TEMPLATE_1 = "template1", "Billing template 1"
        TEMPLATE_2 = "template2", "Billing template 2"

    class HierachyLevelChoices(models.TextChoices):
        Center = "AG", "Agency"
        Delegation = "Dir", "Direction"
        GeneralDirection = "DG", "General Direction"

    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text=_("The organizations that contain this organization"),
    )
    hierarchy_level = models.CharField(
        max_length=3, choices=HierachyLevelChoices.choices
    )
    sub_name = models.CharField(max_length=100, default="")
    country = models.CharField(max_length=100, default="")
    city = models.CharField(max_length=100, default="")
    billing_template_choice = models.CharField(
        choices=BillingTemplateChoices.choices,
        default=BillingTemplateChoices.TEMPLATE_1,
        max_length=50,
    )
    street_address = models.CharField(max_length=100, default="")
    contact_number = models.CharField(max_length=20, default="")
    short_name = models.CharField(max_length=10, default="")
    tax_rate = models.DecimalField(
        max_digits=4,
        default=0,
        decimal_places=2,
        help_text="Tax rate in the following format: 00.00%",
    )
    # Organization data
    contact_email = models.EmailField(max_length=254, unique=True)
    is_online = models.BooleanField(default=False)
    code = models.CharField(max_length=30)

    timezone = TimeZoneField(default="Africa/Douala")

    contribuable = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text=f"This field is Optional",
    )
    logo = models.ImageField(upload_to="distrivite/images", blank=True)
    credential = models.CharField(max_length=20, unique=True)

    objects = OrgManager()

    @property
    def current_subscription(self):
        from apps.subscriptions.models import Subscription

        return (
            Subscription.objects.filter(organization=self.pk)
            .prefetch_related("plan__plan_features")
            .last()
            or None
        )

    class Meta:
        permissions = [
            ("view_organizationdashboard", "Can view organization dashboard"),
        ]

    @cached_property
    def sub_organizations(self):
        return self.children.filter(type=self.TypeChoices.NORMAL)

    @cached_property
    def affiliated_organizations(self):
        return self.children.filter(type=self.TypeChoices.AFFILIATED)

    @cached_property
    # Manager method to get all products in the current and child organizations
    def get_all_products(self):
        # Get the current organization and all its descendants
        return self.get_descendants(include_self=True)

    def __str__(self):
        return f"{self.name} | {self.sub_name}"


class OrganizationGroup(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="organization_groups",
    )
    name = models.CharField(max_length=30, default="")
    is_active = models.BooleanField(default=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    objects = OrgFeatureManager()

    class Meta:
        unique_together = ("organization", "name")

    def __str__(self) -> str:
        return f"{self.organization.name} | {self.name}"


class PermissionMixins(BaseModel):
    groups = models.ManyToManyField(
        OrganizationGroup,
        through="OrganizationUserGroup",
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The organization groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
    )
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("organization user permissions"),
        blank=True,
        help_text=_("Specific permissions for this organization user."),
        # related_name="user_set",
        # related_query_name="user",
    )
    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        help_text=_(
            "Designates that this user has all permissions without "
            "explicitly assigning them."
        ),
    )

    class Meta:
        abstract = True

    def _create_permission_set(self, perms=None):
        """
        Expects a queryset of permissions, returns a formatted
        set.
        """

        if perms is None:
            return set()

        if isinstance(perms, (list, tuple)):
            perms = [(perm.content_type.app_label, perm.codename) for perm in perms]

        else:
            perms = perms.values_list("content_type__app_label", "codename").order_by()

        return set(["%s.%s" % (ct, name) for ct, name in perms])

    def permstr(self, perms):
        return self._create_permission_set(perms)

    def get_user_permissions(self, obj=None):
        """
        Return a list of permission strings that this user has directly.
        Query all available auth backends. If an object is passed in,
        return only permissions matching this object.
        """
        user_perms = self.permissions.all()
        return self._create_permission_set(user_perms)

    def get_group_permissions(self, org_obj=None):
        """
        Return a list of permission strings that this user has through their
        groups. Query all available auth backends. If an object is passed in,
        return only permissions matching this object.
        """

        # superusers get all permissions, like usual
        if self.is_superuser:
            perms = Permission.objects.all()
            return self._create_permission_set(perms)

        # if the user is not in any roles, they get no permissions
        # if not any([user_obj.super_roles.count(), user_obj.roles.count()]):
        if not any([self.groups.count()]):
            return set()

        # at this point, they should have some permissions
        # start off with the set of role permissions

        groups = self.groups.all()
        group_perms = Permission.objects.filter(organizationgroup__in=groups)
        return self._create_permission_set(group_perms)

    def get_all_permissions(self, obj=None):
        user_perms = self.permissions.all()
        groups = self.groups.all()
        group_perms = Permission.objects.filter(organizationgroup__in=groups)
        perms = user_perms | group_perms
        return self._create_permission_set(perms)

    def has_perms(self, perms, obj=None):
        """
        Return True if the user has the specified permission. Query all
        available auth backends, but return immediately if any backend returns
        True. Thus, a user who has permission from a single auth backend is
        assumed to have permission in general. If an object is provided, check
        permissions for that object.
        """

        if not is_iterable(perms) or isinstance(perms, str):
            raise ValueError("perm must be an iterable of permissions.")

        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True
        return any(perm in list(self.get_all_permissions(obj=obj)) for perm in perms)

    def has_module_perms(self, app_label):
        """
        Return True if the user has any permissions in the given app label.
        Use similar logic as has_perm(), above.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        for perm in self.get_all_permissions(obj=None):
            if perm[: perm.index(".")] == app_label:
                return True
        return False


class OrganizationUser(AbstractOrganizationUser, PermissionMixins, BaseModel):
    is_device = models.BooleanField(default=False)
    is_gps_active = models.BooleanField(default=False)
    is_liveness_active = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    can_edit_price = models.BooleanField(default=False)
    can_print_transaction = models.BooleanField(default=False)
    can_print_bill = models.BooleanField(default=False)
    embeddings = models.JSONField(
        default=list, null=True, blank=True
    )  # To store a list of embeddings
    objects = OrgUserManager()

    @property
    def is_owner(self):
        return self.organization.owner.organization_user == self

    def __str__(self) -> str:
        return f"{str(self.user)} | {self.organization.short_name}"


class OrganizationUserGroup(BaseModel):
    group = models.ForeignKey(
        OrganizationGroup,
        on_delete=models.CASCADE,
        related_name="organization_user_groups",
    )
    user = models.ForeignKey(
        OrganizationUser,
        on_delete=models.CASCADE,
        related_name="organization_user_groups",
    )

    def __str__(self) -> str:
        return f"{str(self.group)}|{str(self.user)}"


class OrganizationOwner(AbstractOrganizationOwner, BaseModel):
    objects = OrgOwnerManager()


class OrganizationInvitation(AbstractOrganizationInvitation, BaseModel):
    class InvitationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "Accepted", "Accepted"
        REJECTED = "Rejected", "Rejected"
        EXPIRED = "Expired", "Expired"

    status = models.CharField(
        max_length=10,
        default=InvitationStatus.PENDING,
        choices=InvitationStatus.choices,
    )

    objects = OrgFeatureManager()
