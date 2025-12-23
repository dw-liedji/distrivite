import logging
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import (
    F,
    Prefetch,  # Add this import
)
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.v1.data import serializers
from apps.orders import models as order_models
from apps.organization import mixins as org_mixins
from apps.organization import models as org_models

logger = logging.getLogger(__name__)


class OrganizationUserList(org_mixins.OrganizationAPIUserMixin, generics.ListAPIView):
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


class StockListAPIView(org_mixins.OrganizationAPIUserMixin, generics.ListAPIView):
    """
    API endpoint that returns all batches for the current organization.
    """

    serializer_class = serializers.StockSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]  # Enable later

    def get_queryset(self):
        return (
            order_models.Stock.objects.filter(
                organization=self.request.organization,
                organization_user=self.request.organization_user,
                is_active=True,
            )
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


class StockIdListsView(org_mixins.OrganizationAPIUserMixin, generics.ListAPIView):
    serializer_class = serializers.StockIdSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

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


class UpdateStockQuantityAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def put(self, request, id):
        serializer = serializers.StockQuantityDeltaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        delta = serializer.validated_data["quantity"]

        try:
            with transaction.atomic():
                stock = order_models.Stock.objects.get(
                    id=id, organization=request.organization
                )

                # Event-based quantity update (safe for concurrency)
                stock.quantity = F("quantity") + delta
                stock.save(update_fields=["quantity"])

                # Resolve F() expression
                stock.refresh_from_db(fields=["quantity"])

        except order_models.Stock.DoesNotExist:
            return Response(
                {"detail": "Stock not found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            serializers.StockSerializer(stock).data, status=status.HTTP_200_OK
        )


class CustomerListAPIView(org_mixins.OrganizationAPIUserMixin, generics.ListAPIView):
    """
    API endpoint that returns all batches for the current organization.
    """

    serializer_class = serializers.CustomerSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]  # Enable later

    def get_queryset(self):
        return (
            order_models.Customer.objects.filter(organization=self.request.organization)
            .select_related(
                "organization",
            )
            .order_by("-created")
        )


class CustomerIdListsView(org_mixins.OrganizationAPIUserMixin, generics.ListAPIView):
    serializer_class = serializers.CustomerIdSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

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


class TransactionListAPIView(org_mixins.OrganizationAPIUserMixin, generics.ListAPIView):
    """
    API endpoint that returns all batches for the current organization.
    """

    serializer_class = serializers.TransactionSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]  # Enable later

    def get_queryset(self):
        print("this is the current user:", self.request.user)
        return (
            order_models.Transaction.objects.filter(
                organization=self.request.organization,
                organization_user=self.request.organization_user,
            )
            .select_related(
                "organization",
                "organization_user",
            )
            .order_by("-created")
        )


class TransactionIdListsView(org_mixins.OrganizationAPIUserMixin, generics.ListAPIView):
    serializer_class = serializers.TransactionIdSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return order_models.Transaction.objects.filter(
            organization=self.request.organization,
            organization_user=self.request.organization_user,
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
    Avoids creating duplicate transactions by checking if one exists with the same ID.
    """

    serializer_class = serializers.TransactionSerializer
    pagination_class = None
    # permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):
        # Use client-provided ID to check for duplicates
        transaction_id = serializer.validated_data.get("id")

        obj, created = order_models.Transaction.objects.get_or_create(
            id=transaction_id,
            defaults={
                **serializer.validated_data,
                "organization": self.request.organization,
            },
        )

        if not created:
            # Optionally update existing record with latest data from client
            for attr, value in serializer.validated_data.items():
                setattr(obj, attr, value)
            obj.save()

        return obj

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        output_serializer = self.get_serializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class FacturationListView(org_mixins.OrganizationAPIUserMixin, generics.ListAPIView):
    serializer_class = serializers.FacturationSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Optimized queryset keeping all serializer fields.
        Focus on reducing N+1 queries with proper prefetching.
        """
        # Base filter
        queryset = order_models.Facturation.objects.filter(
            organization=self.request.organization,
            organization_user=self.request.organization_user,
        )

        # CRITICAL: Use select_related for foreign keys (reduces queries for related objects)
        queryset = queryset.select_related(
            "organization",  # For organization.slug
            "customer",  # For customer.name and customer.phone_number
            "organization_user",  # For organization_user_id
            "organization_user__user",  # For organization_user.user.username
        )

        # CRITICAL: Use Prefetch objects to control related queries
        # Optimize FacturationStock queries
        stock_prefetch = Prefetch(
            "facturation_stocks",
            queryset=order_models.FacturationStock.objects.select_related(
                "organization",  # For organization.slug
                "stock",  # For stock_id
                "stock__batch",  # For stock.batch
                "stock__batch__item",  # For stock.batch.item.name
                "organization_user",  # For organization_user_id
            ),
        )

        # Optimize FacturationPayment queries
        payment_prefetch = Prefetch(
            "facturation_payments",
            queryset=order_models.FacturationPayment.objects.select_related(
                "organization",  # For organization.slug
                "organization_user",  # For organization_user_id
            ),
        )

        # Apply both prefetches
        queryset = queryset.prefetch_related(stock_prefetch, payment_prefetch)

        # Order by placed_at descending
        return queryset.order_by("-placed_at")


class FacturationIdListsView(org_mixins.OrganizationAPIUserMixin, generics.ListAPIView):
    serializer_class = serializers.FacturationIdSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return order_models.Facturation.objects.filter(
            organization=self.request.organization
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().values_list("id", flat=True)
        return Response(list(qs))


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


class FacturationCreateView2(generics.CreateAPIView):
    """
    POST /en/<org_slug>/api/v1/data/billing/
    Creates a billing (Facturation) with its items and payments.
    """

    serializer_class = serializers.FacturationSerializer2
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.organization,
            # organization_user=self.request.organization_user,
        )
        return Response


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


class FacturationDeliverView(generics.UpdateAPIView):
    """
    PUT/PATCH /en/<org_slug>/api/v1/data/billing/<id>/edit/
    Updates billing details, items, and payments.
    """

    serializer_class = serializers.FacturationDeliverSerializer
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
