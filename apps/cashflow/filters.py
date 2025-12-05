import django_filters

from apps.cashflow import models
from apps.core.filters import BaseFilter, BaseTransactionFilter
from django_filters import CharFilter, ChoiceFilter, FilterSet, filters
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django_filters.widgets import RangeWidget


class TransactionFilter(BaseFilter, BaseTransactionFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["cash_register"].queryset = (
            models.CashRegister.objects.for_organization(
                organization=self.request.organization
            )
        )

    date_range = filters.DateFromToRangeFilter(
        field_name="created",
        label="Date Range",
        widget=RangeWidget(attrs={"placeholder": "YYYY-MM-DD"}),
    )

    class Meta:
        model = models.Transaction
        fields = ["created", "cash_register", "date_range"]


class DepositFilter(BaseFilter, BaseTransactionFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["cash_register"].queryset = (
            models.CashRegister.objects.for_organization(
                organization=self.request.organization
            )
        )

    search_user = django_filters.CharFilter(
        method="filter_by_user", label="Search Employee"
    )

    def filter_by_user(self, queryset, name, value):
        return queryset.filter(
            Q(organization_user__user__first_name__icontains=value)
            | Q(organization_user__user__last_name__icontains=value)
        )

    class Meta:
        model = models.Deposit
        fields = [
            "created",
            "cash_register",
            "search_user",
        ]


class WithdrawalFilter(BaseFilter, BaseTransactionFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["cash_register"].queryset = (
            models.CashRegister.objects.for_organization(
                organization=self.request.organization
            )
        )

        self.filters["category"].queryset = models.Category.objects.for_organization(
            organization=self.request.organization
        )

    search_user = django_filters.CharFilter(
        method="filter_by_user", label="Search Employee"
    )

    def filter_by_user(self, queryset, name, value):
        return queryset.filter(
            Q(organization_user__user__first_name__icontains=value)
            | Q(organization_user__user__last_name__icontains=value)
        )

    class Meta:
        model = models.Withdrawal
        fields = [
            "created",
            "category",
            "cash_register",
            "search_user",
        ]
