from collections import defaultdict
from decimal import Decimal

from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django_htmx import http as htmx_http

from apps.core import services
from apps.orders import models as order_models

from . import resources as order_resources
from . import views as order_views


class OrgFacturationListExportView(
    order_views.OrgFacturationListView,
):

    def get_queryset(self):
        return (
            order_models.Facturation.objects.filter(
                organization=self.request.organization
            )
            .select_related("organization_user")
            .prefetch_related("facturation_payments")
            .prefetch_related("facturation_stocks")
        )

    def generate_financial_report_simplified(self, filtered_queryset):
        """Simplified approach using the batches data to calculate totals."""

        # 1️⃣ Get all batch data
        batches = (
            order_models.FacturationStock.objects.filter(
                facturation__in=filtered_queryset
            )
            .values(
                "facturation__organization_user_id",
                "facturation__organization_user__user__username",
                "stock__batch__item__name",
            )
            .annotate(
                total_quantity=Sum("quantity", output_field=IntegerField()),
                total_price=Sum(
                    F("quantity") * F("unit_price"),
                    output_field=DecimalField(max_digits=19, decimal_places=6),
                ),
            )
        )

        # 2️⃣ Get payments separately
        payments = (
            order_models.FacturationPayment.objects.filter(
                facturation__in=filtered_queryset
            )
            .values("facturation__organization_user_id")
            .annotate(
                total_paid=Sum(
                    "amount", output_field=DecimalField(max_digits=19, decimal_places=6)
                )
            )
        )

        payment_dict = {
            p["facturation__organization_user_id"]: p["total_paid"] or Decimal(0)
            for p in payments
        }

        # 3️⃣ Build report and calculate totals from batches
        report = defaultdict(
            lambda: {
                "user_name": "",
                "items": [],
                "summary": {
                    "total_items": 0,
                    "total_amount": Decimal(0),
                    "total_paid": Decimal(0),
                    "total_due": Decimal(0),
                },
            }
        )

        for row in batches:
            user_id = row["facturation__organization_user_id"]
            user_entry = report[user_id]

            if not user_entry["user_name"]:
                user_entry["user_name"] = row[
                    "facturation__organization_user__user__username"
                ]

            # Add item details
            user_entry["items"].append(
                {
                    "item_name": row["stock__batch__item__name"],
                    "quantity": row["total_quantity"],
                    "total_price": row["total_price"],
                }
            )

            # Accumulate totals
            user_entry["summary"]["total_items"] += row["total_quantity"]
            user_entry["summary"]["total_amount"] += row["total_price"]

        # 4️⃣ Add payment information
        for user_id, user_entry in report.items():
            total_paid = payment_dict.get(user_id, Decimal(0))
            total_amount = user_entry["summary"]["total_amount"]

            user_entry["summary"]["total_paid"] = total_paid
            user_entry["summary"]["total_due"] = total_amount - total_paid

        return report

    def get(self, request, *args, **kwargs):

        if request.htmx:
            return htmx_http.HttpResponseClientRedirect(request.get_full_path())

        export_format = self.kwargs.get("export_format", "pdf")
        selected_elements = self.request.GET.getlist("selected_elements")
        queryset = None
        if selected_elements:
            queryset = self.get_queryset().filter(id__in=selected_elements)
        else:
            queryset = self.get_queryset()

        filter = self.filterset_class(request.GET, queryset=queryset, request=request)

        filtered_form = filter.form
        filtered_queryset = filter.qs

        filter_form_data_list = []
        if filtered_form.is_valid():
            for (
                field_name,
                field_value,
            ) in filtered_form.cleaned_data.items():
                field_label = filtered_form.fields[field_name].label

                formatted_value = str(field_value)
                if isinstance(field_value, slice):
                    # Check if field_value is a tuple with two datetime values, indicating a date range
                    start = (
                        field_value.start.strftime("%Y-%m-%d")
                        if field_value.start is not None
                        else "None"
                    )
                    stop = (
                        field_value.stop.strftime("%Y-%m-%d")
                        if field_value.stop is not None
                        else "None"
                    )

                    formatted_value = f"From {start} \n to \n {stop}"

                filter_form_data_list.append(
                    {
                        "name": field_name,
                        "label": field_label,
                        "value": formatted_value,
                    }
                )

            if export_format == "user":
                # 1️⃣ Aggregate items sold per user
                # Usage in your view

                report = self.generate_financial_report_simplified(filtered_queryset)

                # context = {
                #     "report": list(batches.values()),
                #     "filtered_form": filtered_form,
                #     "filter_form_data_list": filter_form_data_list,
                # }

                # 4️⃣ Pass context to template
                context = {
                    "report": report.values(),  # list of users
                    "filtered_form": filtered_form,
                    "filter_form_data_list": filter_form_data_list,
                }

                return services.render_pdf(
                    request,
                    "orders/documents/facturation_list_user_print.html",
                    context,
                    "facturation_list_user",
                )
            elif export_format == "pdf":
                # 1. Aggregate Payments - Fixed version
                total_paid_sq = (
                    order_models.FacturationPayment.objects.filter(
                        facturation_id=OuterRef("id")
                    )
                    .values("facturation_id")  # Group by facturation_id
                    .annotate(total_paid=Sum("amount"))
                    .values("total_paid")
                )

                # 2. Aggregate Batches/Items - Fixed version
                total_quantity_sq = (
                    order_models.FacturationStock.objects.filter(
                        facturation_id=OuterRef("id")
                    )
                    .values("facturation_id")  # Group by facturation_id
                    .annotate(total_items=Sum("quantity"))
                    .values("total_items")
                )

                total_amount_sq = (
                    order_models.FacturationStock.objects.filter(
                        facturation_id=OuterRef("id")
                    )
                    .values("facturation_id")  # Group by facturation_id
                    .annotate(total_amount=Sum(F("quantity") * F("unit_price")))
                    .values("total_amount")
                )

                # Calculate facturations with annotations (for individual records)
                facturations = filtered_queryset.annotate(
                    total_amount=Coalesce(
                        Subquery(
                            total_amount_sq,
                            output_field=DecimalField(max_digits=19, decimal_places=6),
                        ),
                        Value(
                            0,
                            output_field=DecimalField(max_digits=19, decimal_places=6),
                        ),
                    ),
                    total_items=Coalesce(
                        Subquery(total_quantity_sq, output_field=IntegerField()),
                        Value(0, output_field=IntegerField()),
                    ),
                    total_paid=Coalesce(
                        Subquery(
                            total_paid_sq,
                            output_field=DecimalField(max_digits=19, decimal_places=6),
                        ),
                        Value(
                            0,
                            output_field=DecimalField(max_digits=19, decimal_places=6),
                        ),
                    ),
                ).annotate(
                    total_due=ExpressionWrapper(
                        F("total_amount") - F("total_paid"),
                        output_field=DecimalField(max_digits=19, decimal_places=6),
                    )
                )

                # BEST APPROACH: Calculate totals directly from related models with proper output_field
                batch_totals = order_models.FacturationStock.objects.filter(
                    facturation_id__in=filtered_queryset.values("id")
                ).aggregate(
                    total_sales_amount=Coalesce(
                        Sum(
                            F("quantity") * F("unit_price"),
                            output_field=DecimalField(max_digits=19, decimal_places=6),
                        ),
                        Value(
                            0,
                            output_field=DecimalField(max_digits=19, decimal_places=6),
                        ),
                    ),
                    total_sales_items=Coalesce(
                        Sum("quantity", output_field=IntegerField()),
                        Value(0, output_field=IntegerField()),
                    ),
                )

                payment_totals = order_models.FacturationPayment.objects.filter(
                    facturation_id__in=filtered_queryset.values("id")
                ).aggregate(
                    grand_total_paid=Coalesce(
                        Sum(
                            "amount",
                            output_field=DecimalField(max_digits=19, decimal_places=6),
                        ),
                        Value(
                            0,
                            output_field=DecimalField(max_digits=19, decimal_places=6),
                        ),
                    ),
                )

                totals = {
                    "total_sales_amount": batch_totals["total_sales_amount"] or 0,
                    "total_sales_count": filtered_queryset.count(),
                    "total_sales_items": batch_totals["total_sales_items"] or 0,
                    "grand_total_paid": payment_totals["grand_total_paid"] or 0,
                }
                totals["grand_total_due"] = (
                    totals["total_sales_amount"] - totals["grand_total_paid"]
                )

                context = {
                    "facturations": facturations,
                    "totals": totals,
                    "filtered_form": filtered_form,
                    "filter_form_data_list": filter_form_data_list,
                }
                return services.render_pdf(
                    request,
                    "orders/documents/facturation_list_print.html",
                    context,
                    f"facturations",
                )


class OrgBatchListExportView(
    order_views.OrgBatchListView,
):
    def get(self, request, *args, **kwargs):

        if request.htmx:
            return htmx_http.HttpResponseClientRedirect(request.get_full_path())

        export_format = self.kwargs.get("export_format", "xlsx")
        selected_elements = self.request.GET.getlist("selected_elements")
        queryset = None
        if selected_elements:
            queryset = self.get_queryset().filter(id__in=selected_elements)
        else:
            queryset = self.get_queryset()

        filter = self.filterset_class(request.GET, queryset=queryset)

        filtered_form = filter.form
        filtered_queryset = filter.qs

        if export_format == "xlsx":
            resource = order_resources.ConsultationResource()
            return services.render_xlsx(
                request,
                resource,
                filtered_queryset,
                f"batchs",
            )
        else:
            context = {
                "batchs": filtered_queryset,
                "filtered_form": filtered_form,
            }

            return services.render_pdf(
                request,
                "orders/documents/batch_list_print.html",
                context,
                f"batchs",
            )


class OrgStockListExportView(
    order_views.OrgStockListView,
):
    def get_queryset(self):
        return (
            order_models.Stock.objects.filter(organization=self.request.organization)
            .select_related("organization_user")
            .select_related("batch__item__category")
            .select_related("organization")
        )

    def get(self, request, *args, **kwargs):

        if request.htmx:
            return htmx_http.HttpResponseClientRedirect(request.get_full_path())

        export_format = self.kwargs.get("export_format", "xlsx")
        selected_elements = self.request.GET.getlist("selected_elements")
        queryset = None
        if selected_elements:
            queryset = self.get_queryset().filter(id__in=selected_elements)
        else:
            queryset = self.get_queryset()

        filter = self.filterset_class(
            request.GET, queryset=queryset, request=self.request
        )

        filtered_form = filter.form
        filtered_queryset = filter.qs

        filter_form_data_list = []
        if filtered_form.is_valid():
            for (
                field_name,
                field_value,
            ) in filtered_form.cleaned_data.items():
                field_label = filtered_form.fields[field_name].label

                formatted_value = str(field_value)
                if isinstance(field_value, slice):
                    # Check if field_value is a tuple with two datetime values, indicating a date range
                    start = (
                        field_value.start.strftime("%Y-%m-%d")
                        if field_value.start is not None
                        else "None"
                    )
                    stop = (
                        field_value.stop.strftime("%Y-%m-%d")
                        if field_value.stop is not None
                        else "None"
                    )

                    formatted_value = f"From {start} \n to \n {stop}"

                filter_form_data_list.append(
                    {
                        "name": field_name,
                        "label": field_label,
                        "value": formatted_value,
                    }
                )

        if export_format == "xlsx":
            resource = order_resources.ConsultationResource()
            return services.render_xlsx(
                request,
                resource,
                filtered_queryset,
                f"batchs",
            )
        else:
            context = {
                "stocks": filtered_queryset,
                "filtered_form": filtered_form,
                "filter_form_data_list": filter_form_data_list,
            }

            return services.render_pdf(
                request,
                "orders/documents/batch_list_print.html",
                context,
                f"stocks",
            )


class OrgTransactionListExportView(
    order_views.OrgTransactionListView,
):
    def get_queryset(self):
        return order_models.Transaction.objects.filter(
            organization=self.request.organization
        ).select_related("organization_user")

    def get(self, request, *args, **kwargs):

        if request.htmx:
            return htmx_http.HttpResponseClientRedirect(request.get_full_path())

        export_format = self.kwargs.get("export_format", "pdf")
        selected_elements = self.request.GET.getlist("selected_elements")
        queryset = None
        if selected_elements:
            queryset = self.get_queryset().filter(id__in=selected_elements)
        else:
            queryset = self.get_queryset()

        filter = self.filterset_class(request.GET, queryset=queryset, request=request)

        filtered_form = filter.form
        filtered_queryset = filter.qs

        filter_form_data_list = []
        if filtered_form.is_valid():
            for (
                field_name,
                field_value,
            ) in filtered_form.cleaned_data.items():
                field_label = filtered_form.fields[field_name].label

                formatted_value = str(field_value)
                if isinstance(field_value, slice):
                    # Check if field_value is a tuple with two datetime values, indicating a date range
                    start = (
                        field_value.start.strftime("%Y-%m-%d")
                        if field_value.start is not None
                        else "None"
                    )
                    stop = (
                        field_value.stop.strftime("%Y-%m-%d")
                        if field_value.stop is not None
                        else "None"
                    )

                    formatted_value = f"From {start} \n to \n {stop}"

                filter_form_data_list.append(
                    {
                        "name": field_name,
                        "label": field_label,
                        "value": formatted_value,
                    }
                )

            if export_format == "user":
                # 1️⃣ Aggregate totals per user per type
                totals = (
                    filtered_queryset.values("organization_user_id")
                    .annotate(
                        total_deposit=Sum(
                            "amount", filter=Q(transaction_type="deposit")
                        ),
                        total_withdrawal=Sum(
                            "amount", filter=Q(transaction_type="withdrawal")
                        ),
                    )
                    .annotate(
                        net_amount=ExpressionWrapper(
                            # Use Coalesce to treat None/NULL values as 0
                            Coalesce(F("total_deposit"), Value(0))
                            - Coalesce(F("total_withdrawal"), Value(0)),
                            output_field=DecimalField(max_digits=19, decimal_places=6),
                        )
                    )
                )

                # Convert to dict for fast lookup
                totals_dict = {t["organization_user_id"]: t for t in totals}

                # 2️⃣ Group transactions per user
                report = defaultdict(
                    lambda: {
                        "user_name": "",
                        "summary": {
                            "total_deposit": Decimal(0),
                            "total_withdrawal": Decimal(0),
                            "net_amount": Decimal(0),
                        },
                        "transactions": [],
                    }
                )

                for tx in filtered_queryset:
                    user_id = tx.organization_user_id
                    user_entry = report[user_id]
                    user_entry["user_name"] = tx.organization_user.user.username

                    # Append transaction
                    user_entry["transactions"].append(
                        {
                            "transaction_broker": tx.transaction_broker,
                            "transaction_type": tx.transaction_type,
                            "amount": tx.amount,
                            "participant": tx.participant,
                            "reason": tx.reason,
                        }
                    )

                # Merge totals
                for user_id, user_entry in report.items():
                    t = totals_dict.get(user_id, {})
                    user_entry["summary"]["total_deposit"] = t.get(
                        "total_deposit"
                    ) or Decimal(0)
                    user_entry["summary"]["total_withdrawal"] = t.get(
                        "total_withdrawal"
                    ) or Decimal(0)
                    user_entry["summary"]["net_amount"] = t.get(
                        "net_amount"
                    ) or Decimal(0)

                # 3️⃣ Compute global totals for header
                global_deposit = sum(
                    u["summary"]["total_deposit"] for u in report.values()
                )
                global_withdrawal = sum(
                    u["summary"]["total_withdrawal"] for u in report.values()
                )
                global_net = sum(u["summary"]["net_amount"] for u in report.values())

                context = {
                    "report": report.values(),  # list of user reports
                    "global_deposit": global_deposit,
                    "global_withdrawal": global_withdrawal,
                    "global_net": global_net,
                    "filter_form_data_list": filter_form_data_list,
                }

                return services.render_pdf(
                    request,
                    "orders/documents/transaction_list_user_print.html",
                    context,
                    "transaction_list_user",
                )

            # fallback
            return HttpResponse("Export format not supported")
