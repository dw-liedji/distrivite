from datetime import date, datetime, timedelta
from decimal import Decimal

import django_filters
from django.db.models import (
    Case,
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django_filters import CharFilter, ChoiceFilter, FilterSet, filters
from django_filters.widgets import RangeWidget
from django_flatpickr import widgets as flatpickr_widgets

from apps.core.filters import BaseFilter

from . import models


class BaseOrganizationFilter(BaseFilter):
    def __init__(self, *args, **kwargs):
        # self.request = kwargs.get(
        #     "request", None
        # )  # Must be pop before the super method

        super().__init__(*args, **kwargs)
        organizations = self.request.organization.get_descendants(include_self=True)
        self.filters["organization"].queryset = (
            models.org_models.Organization.objects.filter(id__in=organizations)
        )

    class Meta:
        model = models.Facturation
        fields = [
            "organization",
            "created",
        ]


class CustomerFilter(BaseFilter):

    name = filters.CharFilter(
        field_name="name",
        label="Nom",
        lookup_expr="icontains",
    )

    phone_number = filters.CharFilter(
        field_name="phone_number",
        label="Téléphone",
        lookup_expr="icontains",
    )

    class Meta:
        model = models.Customer
        fields = ["name", "phone_number"]


class ItemFilter(BaseFilter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters["category"].label = "Category"
        self.filters["category"].queryset = models.Category.objects.filter(
            organization=self.request.organization
        )

    def filter_by_stock_status(self, queryset, name, value):
        queryset = queryset.annotate(
            annotated_total_quantity=Sum(
                Case(
                    When(
                        batchs__expiration_date__gt=datetime.now().date(),
                        then=F("batchs__quantity"),
                    ),
                    default=0,
                )
            )
        )

        if value == "in_stock":
            return queryset.filter(annotated_total_quantity__gt=F("alert_quantity"))
        elif value == "low_stock":
            return queryset.filter(
                annotated_total_quantity__gt=0,
                annotated_total_quantity__lte=F("alert_quantity"),
            )
        elif value == "out_of_stock":
            return queryset.filter(annotated_total_quantity__lte=0)
        return queryset

    def filter_by_name_or_category(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(category__name__icontains=value)
        )

    STOCK_STATUS_CHOICES = (
        ("in_stock", "En stock"),
        ("out_of_stock", "Rupture de stock"),
        ("low_stock", "Alerte de stock"),
    )

    stock_status = ChoiceFilter(
        label="Stock",
        choices=STOCK_STATUS_CHOICES,
        method="filter_by_stock_status",
    )

    name = CharFilter(
        field_name="name",
        label="Article ou Category",
        method="filter_by_name_or_category",
    )

    class Meta:
        model = models.Item
        fields = [
            "category",
            "name",
            # "expiration_date",
        ]


class PrepaidAccountFilter(BaseFilter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters["customer"].label = "Customer"
        self.filters["customer"].queryset = models.Customer.objects.filter(
            organization=self.request.organization
        )

    class Meta:
        model = models.PrepaidAccount
        fields = [
            "customer",
            "amount",
        ]


class CategoryFilter(BaseFilter):

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value))

    name = CharFilter(
        field_name="name",
        label="Name",
        method="filter_by_name",
    )

    class Meta:
        model = models.Category
        fields = [
            # "supplier",
            # "stock_status",
            # "expiration_status",
            "name",
            # "expiration_date",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)  # Pop to avoid passing to super
        super().__init__(*args, **kwargs)


class TransactionFilter(BaseFilter):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.filters["organization_user"].queryset = (
            models.OrganizationUser.objects.filter(
                organization=self.request.organization
            )
        )
        self.filters["organization_user"].label = "User"

    transaction_broker = django_filters.ChoiceFilter(
        choices=models.TransactionBroker.choices, empty_label="All Brokers"
    )

    transaction_type = django_filters.ChoiceFilter(
        choices=models.TransactionType.choices, empty_label="All Types"
    )

    participant = django_filters.CharFilter(
        lookup_expr="icontains", label="Participant Contains"
    )

    reason = django_filters.CharFilter(lookup_expr="icontains", label="Reason Contains")

    created_after = django_filters.DateFilter(
        field_name="created", lookup_expr="gte", label="Created After"
    )

    created_before = django_filters.DateFilter(
        field_name="created", lookup_expr="lte", label="Created Before"
    )

    class Meta:
        model = models.Transaction
        fields = [
            "transaction_broker",
            "transaction_type",
            "organization_user",
            "participant",
            "reason",
            "created_after",
            "created_before",
        ]


class BatchFilter(BaseFilter):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.filters["supplier"].label = "Supplier"
        self.filters["supplier"].queryset = models.Supplier.objects.filter(
            organization=self.request.organization
        )
        self.filters["item__category"].label = "Category"
        self.filters["item__category"].queryset = models.Category.objects.filter(
            organization=self.request.organization
        )

    EXPIRATION_STATUS_CHOICES = (
        ("super_valid", "En Très bon état (plus de 6 mois)"),
        ("valid", "En bon état (en utilisable)"),
        ("expiring_soon", "En cours d'expiration (moins de 6 mois)"),
        ("expired", "Expiré (Non utilisable)"),
    )

    expiration_status = ChoiceFilter(
        label="État d'expiration",
        choices=EXPIRATION_STATUS_CHOICES,
        method="filter_by_expiration_status",
    )

    def filter_by_expiration_status(self, queryset, name, value):
        today = datetime.now().date()
        three_months_later = today + timedelta(days=90 * 2)

        if value == "super_valid":
            return queryset.filter(expiration_date__gt=three_months_later)
        elif value == "valid":
            return queryset.filter(expiration_date__gt=today)
        elif value == "expiring_soon":
            return queryset.filter(
                expiration_date__gt=today, expiration_date__lte=three_months_later
            )
        elif value == "expired":
            return queryset.filter(expiration_date__lt=today)
        return queryset

    def filter_by_name_or_category(self, queryset, name, value):
        return queryset.filter(
            Q(item__name__icontains=value) | Q(item__category__name__icontains=value)
        )

    name = CharFilter(
        field_name="name",
        label="Article ou Category",
        method="filter_by_name_or_category",
    )

    class Meta:
        model = models.Batch
        fields = [
            "supplier",
            "expiration_status",
            "name",
            "item__category",
        ]


class StockFilter(BaseFilter):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.filters["organization_user"].label = "Supplier"
        self.filters["organization_user"].queryset = (
            models.OrganizationUser.objects.filter(
                organization=self.request.organization
            )
        )
        self.filters["batch__item__category"].label = "Category"
        self.filters["batch__item__category"].queryset = models.Category.objects.filter(
            organization=self.request.organization
        )

    EXPIRATION_STATUS_CHOICES = (
        ("super_valid", "En Très bon état (plus de 6 mois)"),
        ("valid", "En bon état (en utilisable)"),
        ("expiring_soon", "En cours d'expiration (moins de 6 mois)"),
        ("expired", "Expiré (Non utilisable)"),
    )

    expiration_status = ChoiceFilter(
        label="État d'expiration",
        choices=EXPIRATION_STATUS_CHOICES,
        method="filter_by_expiration_status",
    )

    def filter_by_expiration_status(self, queryset, name, value):
        today = datetime.now().date()
        three_months_later = today + timedelta(days=90 * 2)

        if value == "super_valid":
            return queryset.filter(batch__expiration_date__gt=three_months_later)
        elif value == "valid":
            return queryset.filter(batch__expiration_date__gt=today)
        elif value == "expiring_soon":
            return queryset.filter(
                batch__expiration_date__gt=today,
                batch__expiration_date__lte=three_months_later,
            )
        elif value == "expired":
            return queryset.filter(batch__expiration_date__lt=today)
        return queryset

    def filter_by_name_or_category(self, queryset, name, value):
        return queryset.filter(
            Q(batch__item__name__icontains=value)
            | Q(batch__item__category__name__icontains=value)
        )

    name = CharFilter(
        field_name="name",
        label="Article ou Category",
        method="filter_by_name_or_category",
    )

    class Meta:
        model = models.Stock
        fields = [
            "organization_user",
            "expiration_status",
            "name",
            "batch__item__category",
        ]


class SupplierFilter(BaseFilter):

    name = CharFilter(
        field_name="name",
        label="Nom",
        lookup_expr="icontains",
    )

    is_active = filters.BooleanFilter(
        field_name="is_active",
        label="Actif",
    )

    class Meta:
        model = models.Supplier
        fields = [
            "is_active",
            "name",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FacturationFilter(BaseFilter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters["organization_user"].queryset = (
            models.OrganizationUser.objects.filter(
                organization=self.request.organization
            )
        )
        self.filters["organization_user"].label = "User"

    customer__name = filters.CharFilter(
        field_name="customer__name",
        label="Nom du client",
        lookup_expr="icontains",
    )

    class Meta:
        model = models.Facturation
        fields = [
            "organization_user",
            "is_delivered",
            "customer__name",
        ]


class FacturationPaymentFilter(BaseFilter):

    customer__name = filters.CharFilter(
        field_name="customer__name",
        label="Nom du patient",
        lookup_expr="icontains",
    )

    payer_field = filters.CharFilter(
        field_name="payer",
        label="Payer",
        method="filter_by_payer",
    )

    def filter_by_payer(self, queryset, name, value):
        return queryset.filter(
            Q(
                Q(organization_user__user__username__icontains=value)
                | Q(organization_user__user__email__icontains=value)
            )
        )

    class Meta:
        model = models.FacturationPayment
        fields = [
            "transaction_broker",
            "payer_field",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SupplierPaymentFilter(BaseFilter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["cash_register"].queryset = (
            models.cashflow_models.CashRegister.objects.filter(
                organization=self.request.organization
            )
        )

    supplier__name = filters.CharFilter(
        field_name="supplier__name",
        label="Supplier",
        lookup_expr="icontains",
    )

    payer_field = filters.CharFilter(
        field_name="payer",
        label="Payer",
        method="filter_by_payer",
    )

    def filter_by_payer(self, queryset, name, value):
        return queryset.filter(
            Q(Q(first_name__icontains=value) | Q(last_name__icontains=value))
        )

    class Meta:
        model = models.SupplierPayment
        fields = [
            "cash_register",
            "supplier__name",
            "payer_field",
        ]


class FacturationRefundFilter(BaseFilter):

    customer__name = filters.CharFilter(
        field_name="customer__name",
        label="Nom du client",
        lookup_expr="icontains",
    )

    class Meta:
        model = models.FacturationRefund
        fields = [
            "customer__name",
            "organization_user",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters["organization_user"].queryset = (
            models.OrganizationUser.objects.filter(
                organization=self.request.organization
            )
        )
        self.filters["organization_user"].label = "Reducer"
