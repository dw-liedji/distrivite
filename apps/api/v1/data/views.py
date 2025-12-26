import logging
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    Prefetch,  # Add this import
    Subquery,
    Sum,
)
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import generics, permissions, status
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
            return obj

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
        # Serialize BEFORE deletion
        serializer = self.get_serializer(instance)
        serialized_data = serializer.data

        # Perform deletion
        self.perform_destroy(instance)

        return Response(serialized_data, status=status.HTTP_200_OK)


class BulkCreditPaymentListAPIView(
    org_mixins.OrganizationAPIUserMixin, generics.ListAPIView
):
    """
    API endpoint that returns all bulk credit payments for the current organization.
    GET /en/<org_slug>/api/v1/data/bulk-credit-payments/
    """

    serializer_class = serializers.BulkCreditPaymentSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            order_models.BulkCreditPayment.objects.filter(
                organization=self.request.organization,
                organization_user=self.request.organization_user,
            )
            .select_related(
                "customer",
                "organization",
                "organization_user",
            )
            .order_by("-created")
        )


class BulkCreditPaymentIdListView(
    org_mixins.OrganizationAPIUserMixin, generics.ListAPIView
):
    """
    GET /en/<org_slug>/api/v1/data/bulk-credit-payment-ids/
    Returns only IDs of bulk credit payments for sync.
    """

    serializer_class = serializers.BulkCreditPaymentIdSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return order_models.BulkCreditPayment.objects.filter(
            organization=self.request.organization,
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().values_list("id", flat=True)
        return Response(list(qs))


class BulkCreditPaymentChangesView(BulkCreditPaymentListAPIView):
    """
    API endpoint to get bulk credit payments changed since a specific timestamp
    GET /en/<org_slug>/api/v1/data/bulk-credit-payment-changes/
    """

    def get_queryset(self):
        since_timestamp = self.request.GET.get("since")

        if not since_timestamp:
            logger.warning(
                "No 'since' parameter provided, returning all bulk credit payments"
            )
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
                f"Fetching bulk credit payments changed since {since_date} (timestamp: {since_timestamp})"
            )

            # Get the base queryset from parent
            queryset = super().get_queryset()

            # Filter payments updated after the given timestamp
            queryset = queryset.filter(modified__gt=since_date)

            changes_count = queryset.count()
            logger.info(
                f"Found {changes_count} bulk credit payments changed since {since_date}"
            )

            return queryset

        except (ValueError, TypeError) as e:
            logger.error(f"Invalid timestamp '{since_timestamp}': {e}")
            # Fallback to returning all payments
            return super().get_queryset()


class BulkCreditPaymentCreateView(generics.CreateAPIView):
    """
    POST /en/<org_slug>/api/v1/data/bulk-credit-payments/create/
    Creates a bulk credit payment.
    Avoids creating duplicate payments by checking if one exists with the same ID.
    """

    serializer_class = serializers.BulkCreditPaymentSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):
        # Use client-provided ID to check for duplicates
        payment_id = serializer.validated_data.get("id")

        # Check if already exists first
        if (
            payment_id
            and order_models.BulkCreditPayment.objects.filter(id=payment_id).exists()
        ):
            # Return existing object with 200 OK (idempotent)
            existing = order_models.BulkCreditPayment.objects.get(id=payment_id)
            return existing

        # Create new payment
        obj = order_models.BulkCreditPayment.objects.create(
            **serializer.validated_data,
            organization=self.request.organization,
        )

        customer = obj.customer

        # Get unpaid facturations
        unpaid_facturations = self._get_unpaid_facturations(customer)

        # if not unpaid_facturations:
        #     messages.warning(
        #         self.request,
        #         f"Le client {customer.name} n'a aucune facture impayée.",
        #     )
        #     # You might want to redirect or handle this case
        #     return self.form_invalid(form)

        # Calculate total outstanding
        # total_outstanding = sum(
        #     facturation.remaining_balance for facturation in unpaid_facturations
        # )

        # Allocate payments
        remaining_amount = obj.amount
        allocations = {}
        payments_to_create = []

        for facturation in unpaid_facturations:
            if remaining_amount <= 0:
                break

            allocate_amount = min(remaining_amount, facturation.remaining_balance)

            if allocate_amount > 0:
                payments_to_create.append(
                    order_models.FacturationPayment(
                        facturation=facturation,
                        organization=facturation.organization,
                        bulk_credit_payment=obj,
                        organization_user=obj.organization_user,
                        transaction_broker=obj.transaction_broker,
                        amount=allocate_amount,
                    )
                )
                allocations[facturation.id] = allocate_amount
                remaining_amount -= allocate_amount

        # Bulk create payments
        if payments_to_create:
            order_models.FacturationPayment.objects.bulk_create(payments_to_create)

        # Create transaction
        order_models.Transaction.objects.create(
            organization=self.request.organization,
            organization_user=obj.organization_user,
            amount=obj.amount,
            transaction_broker=obj.transaction_broker,
            transaction_type=order_models.TransactionType.DEPOSIT,
            participant=str(customer),
            reason=f"Recouvrement de {str(customer)}",
        )

        # Handle results
        total_allocated = sum(allocations.values())
        leftover = obj.amount - total_allocated

        if leftover > 0:
            customer.prepaid_amount = customer.prepaid_amount + leftover
            customer.save()
            # print(f"Montant restant: {leftover}. Créé comme crédit client.")

        # Store for success page
        # self.request.session["last_bulk_payment_id"] = bulk_credit_payment.id

        return obj

    def _get_unpaid_facturations(self, customer):
        """
        Get unpaid facturations using subqueries to calculate:
        - total_paid: Sum of all payments for the facturation
        - total_sales: Sum of (unit_price * quantity) for all facturation_stocks
        """

        # Subquery to calculate total paid for each facturation
        total_paid_subquery = (
            order_models.FacturationPayment.objects.filter(
                facturation_id=OuterRef("pk")
            )
            .values("facturation_id")
            .annotate(
                total=Sum(
                    "amount", output_field=DecimalField(max_digits=19, decimal_places=4)
                )
            )
            .values("total")[:1]
        )

        # Subquery to calculate total sales (unit_price * quantity) for each facturation
        total_sales_subquery = (
            order_models.FacturationStock.objects.filter(facturation_id=OuterRef("pk"))
            .values("facturation_id")
            .annotate(
                total=Sum(
                    F("unit_price") * F("quantity"),
                    output_field=DecimalField(max_digits=19, decimal_places=4),
                )
            )
            .values("total")[:1]
        )

        # Get facturations with annotations
        unpaid_facturations = (
            order_models.Facturation.objects.filter(
                organization=self.request.organization,
                customer=customer,
                is_proforma=False,
            )
            .annotate(
                # Annotate with total paid using Coalesce to handle None values
                total_paid=Coalesce(
                    Subquery(total_paid_subquery),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=19, decimal_places=4),
                ),
                # Annotate with total sales using Coalesce to handle None values
                total_sales=Coalesce(
                    Subquery(total_sales_subquery),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=19, decimal_places=4),
                ),
                # Calculate remaining balance
                remaining_balance=ExpressionWrapper(
                    F("total_sales") - F("total_paid"),
                    output_field=DecimalField(max_digits=19, decimal_places=4),
                ),
            )
            .filter(
                remaining_balance__gt=0  # Only get facturations with positive balance
            )
            .order_by("placed_at")
        )  # Oldest first (FIFO)

        return unpaid_facturations

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)

        output_serializer = self.get_serializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class BulkCreditPaymentUpdateView(generics.UpdateAPIView):
    """
    PUT /en/<org_slug>/api/v1/data/bulk-credit-payments/{id}/edit/
    Updates a bulk credit payment.
    """

    serializer_class = serializers.BulkCreditPaymentSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return order_models.BulkCreditPayment.objects.filter(
            organization=self.request.organization,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class BulkCreditPaymentDeleteView(generics.DestroyAPIView):
    """
    DELETE /en/<org_slug>/api/v1/data/bulk-credit-payments/{id}/delete/
    Deletes a bulk credit payment.
    """

    serializer_class = serializers.BulkCreditPaymentSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return order_models.BulkCreditPayment.objects.filter(
            organization=self.request.organization,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Serialize BEFORE deletion
        serializer = self.get_serializer(instance)
        serialized_data = serializer.data

        # Perform deletion
        self.perform_destroy(instance)

        return Response(serialized_data, status=status.HTTP_200_OK)
