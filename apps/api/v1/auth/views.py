from django.contrib.auth.models import Group
from django.db.models import BooleanField, Case, Q, Value, When
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, serializers, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.organization.models import (  # Replace 'your_app.models' with the actual import path
    Organization,
    OrganizationUser,
)
from apps.users.models import User

from .serializers import (
    AuthOrgUserSerializer,
    AuthOrgUserSerializer2,
    GroupSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_superuser"]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserOrganizationPagination(PageNumberPagination):
    page_size = 30


@api_view(["POST"])
def verify_org(request):
    credential = request.data.get("credential")
    user_id = request.data.get("user_id")

    try:
        # current_datetime = datetime.now()
        # Serialize the updated user
        organizationUser = OrganizationUser.objects.get(
            user_id=user_id, organization__credential=credential
        )

        organization_user_serializer = AuthOrgUserSerializer(organizationUser)
        # print(organization_user_serializer.data)
        return Response(organization_user_serializer.data, status=status.HTTP_200_OK)
    except OrganizationUser.DoesNotExist:
        return Response(
            {"error": "Wrong credentials. Authentication failled found"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
def verify_org2(request):
    credential = request.data.get("credential")
    user_id = request.data.get("user_id")

    try:
        # current_datetime = datetime.now()
        # Serialize the updated user
        organizationUser = OrganizationUser.objects.get(
            user_id=user_id, organization__credential=credential
        )

        organization_user_serializer = AuthOrgUserSerializer2(organizationUser)
        print(organization_user_serializer.data)
        return Response(organization_user_serializer.data, status=status.HTTP_200_OK)
    except OrganizationUser.DoesNotExist:
        return Response(
            {"error": "Wrong credentials. Authentication failled found"},
            status=status.HTTP_404_NOT_FOUND,
        )
