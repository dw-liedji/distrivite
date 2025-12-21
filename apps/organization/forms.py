from django import forms
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.text import slugify

from apps.organization.models import (
    Organization,
    OrganizationGroup,
    OrganizationInvitation,
    OrganizationUser,
    OrganizationUserGroup,
)
from apps.organization.widgets import TabularPermissionsWidget

FORBIDDEN_SLUGS = [
    "api",
    "admin",
    "organization",
    "settings",
    "user",
    "developer",
    "media",
    "static",
    "develop",
]


def validate_organization_name(organization_name):
    if slugify(organization_name) in FORBIDDEN_SLUGS:
        raise ValidationError("Name is not available")


class OrganizationForm(ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Organization name",
                # "class": "pa2 input-reset ba br2 bg-transparent w-100",
            }
        ),
        validators=[validate_organization_name],
    )

    class Meta:
        model = Organization
        fields = [
            "sub_name",
            "city",
            "country",
            "street_address",
            "contact_number",
            "short_name",
            "contact_email",
            "credential",
            "timezone",
            "logo",
        ]


class OrganizationUpdateForm(ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Organization name",
                # "class": "pa2 input-reset ba br2 bg-transparent w-100",
            }
        ),
        validators=[validate_organization_name],
    )

    contact_email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "contact@example.com",
                # "class": "pa2 input-reset ba br2 bg-transparent w-100",
            }
        )
    )

    class Meta:
        model = Organization
        fields = [
            "name",
            "sub_name",
            "contact_email",
            "country",
            "city",
            "short_name",
            "credential",
            "street_address",
            "timezone",
            "logo",
        ]


class OrganizationUserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        organization_user = kwargs.pop("organization_user", None)
        super(OrganizationUserForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        # self.fields[
        #     "groups"
        # ].queryset = OrganizationGroup.objects.for_organization(
        #     organization=organization
        # ).select_related(
        #     "organization"
        # )
        # self.fields["groups"].initial = 0

        self.fields["permissions"].help_text = None
        self.fields["permissions"].label = "user permissions"
        self.fields["permissions"].queryset = Permission.objects.select_related(
            "content_type",
        ).all()

    class Meta:
        model = OrganizationUser
        fields = [
            "organization",
            "is_admin",
            "is_active",
            "is_device",
            "is_gps_active",
            "is_liveness_active",
            "is_manager",
            "can_edit_price",
            "can_print_transaction",
            "can_print_bill",
            # "groups",
            "permissions",
        ]

        widgets = {
            "permissions": TabularPermissionsWidget(
                "organization user permissions", "permissions"
            ),
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            # "groups": forms.CheckboxSelectMultiple(),
        }


class OrganizationUserAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        organization_user = kwargs.pop("organization_user", None)
        super(OrganizationUserAddForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        # self.fields["permissions"].help_text = None
        # self.fields["permissions"].label = "user permissions"
        # self.fields["permissions"].queryset = Permission.objects.select_related(
        #     "content_type",
        # ).all()

    class Meta:
        model = OrganizationUser
        fields = [
            "organization",
            "is_admin",
            "is_active",
            "is_device",
            "is_gps_active",
            "is_liveness_active",
            "is_manager",
            "can_edit_price",
            "can_print_transaction",
            "can_print_bill",
            # "groups",
            # "permissions",
        ]

        widgets = {
            # "permissions": TabularPermissionsWidget(
            #     "organization user permissions", "permissions"
            # ),
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            # "groups": forms.CheckboxSelectMultiple(),
        }


class OrganizationUserChangeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        organization_user = kwargs.pop("organization_user", None)
        super(OrganizationUserChangeForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["permissions"].help_text = None
        self.fields["permissions"].label = "user permissions"
        self.fields["permissions"].queryset = Permission.objects.select_related(
            "content_type",
        ).all()

    class Meta:
        model = OrganizationUser
        fields = [
            "organization",
            "is_admin",
            "is_active",
            "is_device",
            "is_gps_active",
            "is_liveness_active",
            "is_manager",
            "can_edit_price",
            "can_print_transaction",
            "can_print_bill",
            "groups",
            "permissions",
        ]

        widgets = {
            "permissions": TabularPermissionsWidget(
                "organization user permissions", "permissions"
            ),
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "groups": forms.CheckboxSelectMultiple(),
        }


class OrganizationGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        organization_user = kwargs.pop("organization_user", None)
        super(OrganizationGroupForm, self).__init__(*args, **kwargs)
        self.fields[
            "organization"
        ].initial = organization  # Used when submitting the form (clean method)
        self.fields["organization"].label = ""
        self.fields["permissions"].help_text = None
        self.fields["permissions"].label = "group permissions"
        self.fields["permissions"].queryset = Permission.objects.select_related(
            "content_type",
        ).all()

    class Meta:
        model = OrganizationGroup
        fields = ["organization", "name", "permissions"]

        widgets = {
            "permissions": TabularPermissionsWidget(
                "organization group permissions", "permissions"
            ),
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
        }


class OrganizationUserGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        organization_user = kwargs.pop("organization_user", None)
        group = kwargs.pop("group", None)
        super(OrganizationUserGroupForm, self).__init__(*args, **kwargs)
        self.fields["user"].queryset = OrganizationUser.objects.for_organization(
            organization=organization
        ).all()

        self.fields[
            "group"
        ].initial = group  # Used when submitting the form (clean method)
        self.fields["group"].label = ""

    class Meta:
        model = OrganizationUserGroup
        fields = ["user", "group"]

        widgets = {
            # "organization": forms.TextInput(
            #     attrs={
            #         "class": "is-hidden",
            #     }
            # ),
            "group": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
        }


class OrganizationInvitationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        organization_user = kwargs.pop("organization_user", None)
        super(OrganizationInvitationForm, self).__init__(*args, **kwargs)
        self.fields[
            "organization"
        ].initial = organization  # Used when submitting the form (clean method)
        self.fields["organization"].label = ""
        self.fields["invited_by"].initial = organization_user.user
        self.fields["invited_by"].label = ""

    class Meta:
        model = OrganizationInvitation
        fields = ["organization", "invited_by", "invitee_identifier"]

        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "invited_by": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
        }
