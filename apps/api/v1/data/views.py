from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import BooleanField, Case, Q, Value, When
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from twilio.rest import Client

from apps.api.v1.data import serializers
from apps.orders import models as order_models
from apps.organization import models as org_models
from apps.users.models import User


class OrganizationUserList(generics.ListAPIView):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    pagination_class = None

    def get_queryset(self):
        return (
            org_models.OrganizationUser.objects.filter(
                organization=self.request.organization
            )
            .select_related(
                "user",
                "organization",
            )
            .order_by("-created")
        )

    serializer_class = serializers.OrganizationUserSerializer
    # permission_classes = [permissions.IsAuthenticated] add authentication in future to authenticate the organization (virtual user)


class StockListAPIView(generics.ListAPIView):
    """
    API endpoint that returns all batches for the current organization.
    """

    serializer_class = serializers.StockSerializer
    pagination_class = None
    # permission_classes = [permissions.IsAuthenticated]  # Enable later

    def get_queryset(self):
        return (
            order_models.Stock.objects.filter(organization=self.request.organization)
            .select_related(
                "batch__organization",
                "batch__item",
                "batch__item__category",
                "batch__supplier",
                "batch__last_maintainer",
                "batch__last_maintainer__user",
            )
            .order_by("-created")
        )


class StockIdListsView(generics.ListAPIView):
    serializer_class = serializers.StockIdSerializer
    pagination_class = None

    def get_queryset(self):
        return order_models.Stock.objects.filter(organization=self.request.organization)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().values_list("id", flat=True)
        return Response(list(qs))


class StockChangesView(StockListAPIView):
    """
    API endpoint to get facturations changed since a specific timestamp
    """

    def get_queryset(self):
        since_timestamp = self.request.GET.get("since")

        if not since_timestamp:
            logger.warning("No 'since' parameter provided, returning all facturations")
            return super().get_queryset()

        try:
            # Convert milliseconds timestamp to datetime
            since_timestamp = int(since_timestamp)

            # Handle milliseconds (Android sends milliseconds)
            if since_timestamp > 1000000000:  # It's in milliseconds
                since_timestamp_seconds = since_timestamp / 1000.0
            else:  # It's in seconds
                since_timestamp_seconds = since_timestamp

            # Create timezone-aware datetime
            since_date = datetime.fromtimestamp(
                since_timestamp_seconds, tz=timezone.utc
            )

            logger.info(
                f"Fetching facturations changed since {since_date} (timestamp: {since_timestamp})"
            )

            # Get the base queryset from parent
            queryset = super().get_queryset()

            # Filter facturations updated after the given timestamp
            # Assuming you have updated_at field, if not, use created_at or placed_at
            queryset = queryset.filter(modified__gt=since_date)

            changes_count = queryset.count()
            logger.info(
                f"Found {changes_count} facturations changed since {since_date}"
            )

            return queryset

        except (ValueError, TypeError) as e:
            logger.error(f"Invalid timestamp '{since_timestamp}': {e}")
            # Fallback to returning all facturations
            return super().get_queryset()


class CustomerListAPIView(generics.ListAPIView):
    """
    API endpoint that returns all batches for the current organization.
    """

    serializer_class = serializers.CustomerSerializer
    pagination_class = None
    # permission_classes = [permissions.IsAuthenticated]  # Enable later

    def get_queryset(self):
        return (
            order_models.Customer.objects.filter(organization=self.request.organization)
            .select_related(
                "organization",
            )
            .order_by("-created")
        )


class CustomerIdListsView(generics.ListAPIView):
    serializer_class = serializers.CustomerIdSerializer
    pagination_class = None

    def get_queryset(self):
        return order_models.Customer.objects.filter(
            organization=self.request.organization
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().values_list("id", flat=True)
        return Response(list(qs))


class CustomerChangesView(CustomerListAPIView):
    """
    API endpoint to get facturations changed since a specific timestamp
    """

    def get_queryset(self):
        since_timestamp = self.request.GET.get("since")

        if not since_timestamp:
            logger.warning("No 'since' parameter provided, returning all facturations")
            return super().get_queryset()

        try:
            # Convert milliseconds timestamp to datetime
            since_timestamp = int(since_timestamp)

            # Handle milliseconds (Android sends milliseconds)
            if since_timestamp > 1000000000:  # It's in milliseconds
                since_timestamp_seconds = since_timestamp / 1000.0
            else:  # It's in seconds
                since_timestamp_seconds = since_timestamp

            # Create timezone-aware datetime
            since_date = datetime.fromtimestamp(
                since_timestamp_seconds, tz=timezone.utc
            )

            logger.info(
                f"Fetching facturations changed since {since_date} (timestamp: {since_timestamp})"
            )

            # Get the base queryset from parent
            queryset = super().get_queryset()

            # Filter facturations updated after the given timestamp
            # Assuming you have updated_at field, if not, use created_at or placed_at
            queryset = queryset.filter(modified__gt=since_date)

            changes_count = queryset.count()
            logger.info(
                f"Found {changes_count} facturations changed since {since_date}"
            )

            return queryset

        except (ValueError, TypeError) as e:
            logger.error(f"Invalid timestamp '{since_timestamp}': {e}")
            # Fallback to returning all facturations
            return super().get_queryset()


class CustomerCreateView(generics.CreateAPIView):
    """
    POST /en/<org_slug>/api/v1/data/billing/
    Creates a billing (Facturation) with its items and payments.
    """

    serializer_class = serializers.CustomerSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


class TransactionListAPIView(generics.ListAPIView):
    """
    API endpoint that returns all batches for the current organization.
    """

    serializer_class = serializers.TransactionSerializer
    pagination_class = None
    # permission_classes = [permissions.IsAuthenticated]  # Enable later

    def get_queryset(self):
        return (
            order_models.Transaction.objects.filter(
                organization=self.request.organization
            )
            .select_related(
                "organization",
                "organization_user",
            )
            .order_by("-created")
        )


class TransactionIdListsView(generics.ListAPIView):
    serializer_class = serializers.TransactionIdSerializer
    pagination_class = None

    def get_queryset(self):
        return order_models.Transaction.objects.filter(
            organization=self.request.organization
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().values_list("id", flat=True)
        return Response(list(qs))


class TransactionChangesView(TransactionListAPIView):
    """
    API endpoint to get facturations changed since a specific timestamp
    """

    def get_queryset(self):
        since_timestamp = self.request.GET.get("since")

        if not since_timestamp:
            logger.warning("No 'since' parameter provided, returning all facturations")
            return super().get_queryset()

        try:
            # Convert milliseconds timestamp to datetime
            since_timestamp = int(since_timestamp)

            # Handle milliseconds (Android sends milliseconds)
            if since_timestamp > 1000000000:  # It's in milliseconds
                since_timestamp_seconds = since_timestamp / 1000.0
            else:  # It's in seconds
                since_timestamp_seconds = since_timestamp

            # Create timezone-aware datetime
            since_date = datetime.fromtimestamp(
                since_timestamp_seconds, tz=timezone.utc
            )

            logger.info(
                f"Fetching facturations changed since {since_date} (timestamp: {since_timestamp})"
            )

            # Get the base queryset from parent
            queryset = super().get_queryset()

            # Filter facturations updated after the given timestamp
            # Assuming you have updated_at field, if not, use created_at or placed_at
            queryset = queryset.filter(modified__gt=since_date)

            changes_count = queryset.count()
            logger.info(
                f"Found {changes_count} facturations changed since {since_date}"
            )

            return queryset

        except (ValueError, TypeError) as e:
            logger.error(f"Invalid timestamp '{since_timestamp}': {e}")
            # Fallback to returning all facturations
            return super().get_queryset()


class TransactionCreateView(generics.CreateAPIView):
    """
    POST /en/<org_slug>/api/v1/data/billing/
    Creates a billing (Facturation) with its items and payments.
    """

    serializer_class = serializers.TransactionSerializer
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.organization,
        )


class FacturationListView(generics.ListAPIView):
    serializer_class = serializers.FacturationSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            order_models.Facturation.objects.filter(
                organization=self.request.organization
            )
            .select_related("organization_user", "organization")
            .prefetch_related("facturation_stocks", "facturation_payments")
            .order_by("-placed_at")
        )


class FacturationIdListsView(generics.ListAPIView):
    serializer_class = serializers.FacturationIdSerializer
    pagination_class = None

    def get_queryset(self):
        return order_models.Facturation.objects.filter(
            organization=self.request.organization
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().values_list("id", flat=True)
        return Response(list(qs))


import logging
from datetime import datetime

from django.utils import timezone

logger = logging.getLogger(__name__)


class FacturationChangesView(FacturationListView):
    """
    API endpoint to get facturations changed since a specific timestamp
    """

    def get_queryset(self):
        since_timestamp = self.request.GET.get("since")

        if not since_timestamp:
            logger.warning("No 'since' parameter provided, returning all facturations")
            return super().get_queryset()

        try:
            # Convert milliseconds timestamp to datetime
            since_timestamp = int(since_timestamp)

            # Handle milliseconds (Android sends milliseconds)
            if since_timestamp > 1000000000:  # It's in milliseconds
                since_timestamp_seconds = since_timestamp / 1000.0
            else:  # It's in seconds
                since_timestamp_seconds = since_timestamp

            # Create timezone-aware datetime
            since_date = datetime.fromtimestamp(
                since_timestamp_seconds, tz=timezone.utc
            )

            logger.info(
                f"Fetching facturations changed since {since_date} (timestamp: {since_timestamp})"
            )

            # Get the base queryset from parent
            queryset = super().get_queryset()

            # Filter facturations updated after the given timestamp
            # Assuming you have updated_at field, if not, use created_at or placed_at
            queryset = queryset.filter(modified__gt=since_date)

            changes_count = queryset.count()
            logger.info(
                f"Found {changes_count} facturations changed since {since_date}"
            )

            return queryset

        except (ValueError, TypeError) as e:
            logger.error(f"Invalid timestamp '{since_timestamp}': {e}")
            # Fallback to returning all facturations
            return super().get_queryset()


class FacturationCreateView(generics.CreateAPIView):
    """
    POST /en/<org_slug>/api/v1/data/billing/
    Creates a billing (Facturation) with its items and payments.
    """

    serializer_class = serializers.FacturationSerializer
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def perform_create(self, serializer):

        serializer.save(
            organization=self.request.organization,
            # organization_user=self.request.organization_user,
        )


class FacturationUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH /en/<org_slug>/api/v1/data/billing/<id>/edit/
    Updates billing details, items, and payments.
    """

    serializer_class = serializers.FacturationSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            order_models.Facturation.objects.filter(
                organization=self.request.organization
            )
            .select_related("organization_user", "organization")
            .prefetch_related("facturation_stocks", "facturation_payments")
        )

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)


class FacturationRetrieveView(generics.RetrieveAPIView):
    """
    GET /en/<org_slug>/api/v1/data/billing/<id>/
    Retrieves a billing with its items and payments.
    """

    serializer_class = serializers.FacturationSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            order_models.Facturation.objects.filter(
                organization=self.request.organization
            )
            .select_related("organization_user", "medical_visit")
            .prefetch_related("facturation_stocks", "facturation_payments")
        )


class FacturationDeleteView(generics.DestroyAPIView):
    """
    DELETE /en/<org_slug>/api/v1/data/billing/<id>/delete/
    Deletes a billing and its related items/payments.
    """

    serializer_class = serializers.FacturationSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return order_models.Facturation.objects.filter(
            organization=self.request.organization
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


from decimal import Decimal

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["POST"])
@transaction.atomic
def make_payment(request):
    org_slug = request.data.get("org_slug")
    customer_id = request.data.get("customer_id")
    amount = request.data.get("amount")

    organization = request.organization

    try:

        # Get or create prepaid account
        account, created = order_models.PrepaidAccount.objects.get_or_create(
            customer_id=customer_id, organization=organization, defaults={"amount": 0}
        )

        # Check if sufficient balance
        if account.amount < Decimal(amount):
            return Response(
                {"org_slug": org_slug, "customer_id": customer_id, "is_paid": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Deduct amount from prepaid account
        account.amount -= Decimal(amount)
        account.save()

        return Response(
            {"org_slug": org_slug, "customer_id": customer_id, "is_paid": True}
        )

    except order_models.Customer.DoesNotExist:
        return Response(
            {"org_slug": org_slug, "customer_id": customer_id, "is_paid": False},
            status=status.HTTP_404_NOT_FOUND,
        )
