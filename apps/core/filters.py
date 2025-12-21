from datetime import date, timedelta

from django_filters import ChoiceFilter, FilterSet, filters
from django_filters.widgets import DateRangeWidget
from django_flatpickr import widgets as flatpickr_widgets

from apps.core import models


class BaseFilter(FilterSet):
    date_field = filters.DateFilter(
        field_name="created",
        label="Date",
        method="filter_by_date",
    )
    created = ChoiceFilter(
        label="Period",
        choices=(
            ("today", "Today"),
            ("this_week", "This week"),
            ("last_week", "Last week"),  # Add "Last week" as a filter option
            ("this_month", "This month"),
            ("this_year", "This year"),
        ),
        method="filter_by_date_range",
    )

    date_range = filters.DateFromToRangeFilter(
        field_name="created",
        label="Date Range",
        widget=DateRangeWidget(attrs={"placeholder": "YYYY-MM-DD", "type": "date"}),
    )

    def filter_by_date(self, queryset, name, value):
        return queryset.filter(**{f"{name}__date": value})

    def filter_by_date_range(self, queryset, name, value):
        if value == "today":
            return queryset.filter(**{f"{name}__date": date.today()})
        elif value == "this_week":
            start_of_week = date.today() - timedelta(days=date.today().weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return queryset.filter(
                **{
                    f"{name}__gte": start_of_week,
                    f"{name}__lte": end_of_week,
                }
            )
        elif value == "last_week":  # Add handling for "last_week" value
            end_of_last_week = date.today() - timedelta(days=date.today().weekday() + 1)
            start_of_last_week = end_of_last_week - timedelta(days=6)
            return queryset.filter(
                **{
                    f"{name}__gte": start_of_last_week,
                    f"{name}__lte": end_of_last_week,
                }
            )
        elif value == "this_month":
            return queryset.filter(
                **{
                    f"{name}__year": date.today().year,
                    f"{name}__month": date.today().month,
                }
            )
        elif value == "this_year":
            return queryset.filter(**{f"{name}__year": date.today().year})
        else:
            return queryset

    class Meta:
        model = models.BaseModel
        fields = ["created", "date_range"]


class BaseTransactionFilter(FilterSet):
    accounting_date = ChoiceFilter(
        label="Transaction Period",
        choices=(
            ("today", "Today"),
            ("this_week", "This week"),
            ("last_week", "Last week"),  # Add "Last week" as a filter option
            ("this_month", "This month"),
            ("this_year", "This year"),
        ),
        method="filter_by_accounting_date_range",
    )

    field_accounting_date = filters.DateFilter(
        field_name="accounting_date",
        label="Transaction Date",
        widget=flatpickr_widgets.DatePickerInput(),
        method="filter_by_accounting_date",
    )

    def filter_by_accounting_date(self, queryset, name, value):
        return queryset.filter(**{f"{name}": value})

    def filter_by_accounting_date_range(self, queryset, name, value):
        if value == "today":
            return queryset.filter(**{f"{name}": date.today()})
        elif value == "this_week":
            start_of_week = date.today() - timedelta(days=date.today().weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return queryset.filter(
                **{
                    f"{name}__gte": start_of_week,
                    f"{name}__lte": end_of_week,
                }
            )
        elif value == "last_week":  # Add handling for "last_week" value
            end_of_last_week = date.today() - timedelta(days=date.today().weekday() + 1)
            start_of_last_week = end_of_last_week - timedelta(days=6)
            return queryset.filter(
                **{
                    f"{name}__gte": start_of_last_week,
                    f"{name}__lte": end_of_last_week,
                }
            )
        elif value == "this_month":
            return queryset.filter(
                **{
                    f"{name}__year": date.today().year,
                    f"{name}__month": date.today().month,
                }
            )
        elif value == "this_year":
            return queryset.filter(**{f"{name}__year": date.today().year})
        else:
            return queryset
