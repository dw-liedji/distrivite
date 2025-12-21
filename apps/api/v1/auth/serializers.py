from django.contrib.auth.models import Group
from rest_framework import serializers

from apps.organization import models as org_models
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    user_permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "groups",
            "user_permissions",
            "is_superuser",
            "is_staff",
        ]

    def get_user_permissions(self, obj):
        return list(
            obj.user_permissions.all()
        )  # I'm not sure list type casting is necessary


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["name"]


class AuthOrgUserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    created = serializers.DateTimeField()
    modified = serializers.DateTimeField()
    org_id = serializers.SerializerMethodField(method_name="get_org_id")
    user_id = serializers.SerializerMethodField(method_name="get_user_id")
    org_slug = serializers.SerializerMethodField(method_name="get_org_slug")
    org_credential = serializers.SerializerMethodField(method_name="get_org_credential")
    name = serializers.SerializerMethodField(method_name="get_name")

    embeddings = serializers.SerializerMethodField(method_name="get_embeddings")
    radius = serializers.SerializerMethodField(method_name="get_radius")
    check_in_latitude = serializers.SerializerMethodField(
        method_name="get_check_in_latitude"
    )
    check_in_longitude = serializers.SerializerMethodField(
        method_name="get_check_in_longitude"
    )
    check_out_latitude = serializers.SerializerMethodField(
        method_name="get_check_out_latitude"
    )
    check_out_longitude = serializers.SerializerMethodField(
        method_name="get_check_out_longitude"
    )

    def get_radius(self, organization_user: org_models.OrganizationUser):
        return 1000.0

    class Meta:
        model = org_models.OrganizationUser
        fields = [
            "id",
            "created",
            "modified",
            "org_id",
            "user_id",
            "org_credential",
            "org_slug",
            "name",
            "is_active",
            "is_admin",
            "is_manager",
            "is_device",
            "is_gps_active",
            "can_edit_price",
            "can_print_transaction",
            "can_print_bill",
            "is_liveness_active",
            "embeddings",
            "radius",
            "check_in_latitude",
            "check_in_longitude",
            "check_out_latitude",
            "check_out_longitude",
        ]

    def get_org_id(self, organization_user: org_models.OrganizationUser):
        return organization_user.organization.id

    def get_org_slug(self, organization_user: org_models.OrganizationUser):
        return organization_user.organization.slug

    def get_org_credential(self, organization_user: org_models.OrganizationUser):
        return organization_user.organization.credential

    def get_name(self, organization_user: org_models.OrganizationUser):
        return organization_user.user.username

    def get_embeddings(self, organization_user: org_models.OrganizationUser):
        return organization_user.embeddings

    def get_user_id(self, organization_user: org_models.OrganizationUser):
        return organization_user.user.id

    def get_check_in_latitude(self, organization_user: org_models.OrganizationUser):
        return 10.0

    def get_check_in_longitude(self, organization_user: org_models.OrganizationUser):
        return 5.10

    def get_check_out_latitude(self, organization_user: org_models.OrganizationUser):
        return 10.2

    def get_check_out_longitude(self, organization_user: org_models.OrganizationUser):
        return 5.0


class AuthOrgUserSerializer2(serializers.ModelSerializer):
    id = serializers.UUIDField()
    created = serializers.DateTimeField()
    modified = serializers.DateTimeField()
    org_id = serializers.SerializerMethodField(method_name="get_org_id")
    user_id = serializers.SerializerMethodField(method_name="get_user_id")
    org_slug = serializers.SerializerMethodField(method_name="get_org_slug")
    org_credential = serializers.SerializerMethodField(method_name="get_org_credential")
    name = serializers.SerializerMethodField(method_name="get_name")
    permissions = serializers.SerializerMethodField(method_name="get_permissions")
    embeddings = serializers.SerializerMethodField(method_name="get_embeddings")
    radius = serializers.SerializerMethodField(method_name="get_radius")
    check_in_latitude = serializers.SerializerMethodField(
        method_name="get_check_in_latitude"
    )
    check_in_longitude = serializers.SerializerMethodField(
        method_name="get_check_in_longitude"
    )
    check_out_latitude = serializers.SerializerMethodField(
        method_name="get_check_out_latitude"
    )
    check_out_longitude = serializers.SerializerMethodField(
        method_name="get_check_out_longitude"
    )

    def get_radius(self, organization_user: org_models.OrganizationUser):
        return 1000.0

    class Meta:
        model = org_models.OrganizationUser
        fields = [
            "id",
            "created",
            "modified",
            "org_id",
            "user_id",
            "org_credential",
            "org_slug",
            "name",
            "is_active",
            "is_admin",
            "is_manager",
            "is_device",
            "is_gps_active",
            "is_liveness_active",
            "permissions",
            "embeddings",
            "radius",
            "check_in_latitude",
            "check_in_longitude",
            "check_out_latitude",
            "check_out_longitude",
        ]

    def get_org_id(self, organization_user: org_models.OrganizationUser):
        return organization_user.organization.id

    def get_org_slug(self, organization_user: org_models.OrganizationUser):
        return organization_user.organization.slug

    def get_org_credential(self, organization_user: org_models.OrganizationUser):
        return organization_user.organization.credential

    def get_name(self, organization_user: org_models.OrganizationUser):
        return organization_user.user.username

    def get_embeddings(self, organization_user: org_models.OrganizationUser):
        return organization_user.embeddings

    def get_permissions(self, organization_user: org_models.OrganizationUser):
        return list(organization_user.permissions)

    def get_user_id(self, organization_user: org_models.OrganizationUser):
        return organization_user.user.id

    def get_check_in_latitude(self, organization_user: org_models.OrganizationUser):
        return 10.0

    def get_check_in_longitude(self, organization_user: org_models.OrganizationUser):
        return 5.10

    def get_check_out_latitude(self, organization_user: org_models.OrganizationUser):
        return 10.2

    def get_check_out_longitude(self, organization_user: org_models.OrganizationUser):
        return 5.0
