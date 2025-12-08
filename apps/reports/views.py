from collections import defaultdict
from decimal import Decimal

from bokeh.models import ColumnDataSource
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    Avg,
    Case,
    Count,
    DecimalField,
    DurationField,
    ExpressionWrapper,
    F,
    Func,
    Q,
    Sum,
    Value,
    When,
    Window,
)
from django.db.models.functions import Coalesce, Concat
from django.shortcuts import HttpResponse, redirect, render
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from apps.cashflow import models as cashflow_models
from apps.core import services
from apps.core.filters import BaseFilter
from apps.orders import models as order_models
from apps.orders import models as orders_models
from apps.orders.filters import BaseOrganizationFilter
from apps.organization.mixins import (
    AdminRequiredMixin,
    MembershipRequiredMixin,
    OrgFormMixin,
)
from apps.organization.models import Organization, OrganizationUser
from apps.reports import plots as report_plots


class OrgTeachingReportView(
    LoginRequiredMixin,
    # MembershipRequiredMixin,
    # AdminRequiredMixin,
    TemplateView,
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, "reports/org_teaching_report.html", context)


class OrgTeachingReportPrintView(OrgTeachingReportView):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return services.render_pdf(
            request,
            "reports/org_teaching_report_print.html",
            context=context,
            output_filename="état-de-sante-de-l'entreprise",
        )


class OrgReportView(
    LoginRequiredMixin,
    # MembershipRequiredMixin,
    # AdminRequiredMixin,
    TemplateView,
):
    template_name = "orders/commercial_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        withdrawals = cashflow_models.Withdrawal.objects.for_organization(
            organization=self.request.organization
        ).all()
        deposits = cashflow_models.Deposit.objects.for_organization(
            organization=self.request.organization
        ).all()

        facturations = order_models.Facturation.objects.filter(
            organization=self.request.organization
        ).all()

        facturation_filter = BaseFilter(self.request.GET, queryset=facturations)

        deposit_filter = BaseFilter(self.request.GET, queryset=deposits)
        withdrawal_filter = BaseFilter(self.request.GET, queryset=withdrawals)

        total_deposits = deposit_filter.qs.count()
        total_withdrawals = withdrawal_filter.qs.count()

        total_deposit_amount = (
            deposit_filter.qs.aggregate(total_amount=Sum("amount"))["total_amount"]
            or 0.0
        )

        total_withdrawal_amount = (
            withdrawal_filter.qs.aggregate(total_amount=Sum("amount"))["total_amount"]
            or 0.0
        )

        total_facturations = facturation_filter.qs.count() or 0

        total_facturation_price = (
            facturation_filter.qs.aggregate(
                total_price=Sum(
                    F("facturation_stocks__unit_price")
                    * F("facturation_stocks__quantity")
                )
            )["total_price"]
            or 0.0
        )

        mixed_total_facturations = total_facturations

        mixed_total_facturation_price = Decimal(total_facturation_price)

        facturation_reports = []
        facturation_reports.append(
            {
                "type": "Vente de produits en espèces",
                "total": total_facturations,
                "total_price": total_facturation_price,
            }
        )

        order_filter = BaseOrganizationFilter(
            self.request.GET,
            queryset=order_models.Facturation.objects.filter(
                organization__in=self.request.organization.get_descendants(
                    include_self=True
                )
            ),
            request=self.request,
        )

        global_deposit = (
            cashflow_models.Deposit.objects.filter(
                organization=self.request.organization
            ).aggregate(total_amount=Sum("amount"))["total_amount"]
            or 0.0
        )

        global_withdrawal = (
            cashflow_models.Withdrawal.objects.filter(
                organization=self.request.organization
            ).aggregate(total_amount=Sum("amount"))["total_amount"]
            or 0.0
        )

        global_balance = Decimal(global_deposit) - Decimal(global_withdrawal)

        # Processing inventory report
        s = order_models.FacturationStock.objects.filter(
            organization=self.request.organization
        )

        inventory = (
            BaseFilter(self.request.GET, queryset=s)
            .qs.values(
                "stock__batch__item__id", "stock__batch__item__name", "stock__quantity"
            )
            .annotate(total_facturation=Coalesce(Sum("quantity"), Value(0)))
        )

        from collections import defaultdict

        # Merge inventories
        merged_inventory = defaultdict(
            lambda: {
                "total_facturation": 0,
                "total": 0,
            }
        )

        for inv in inventory:
            item_id = inv["stock__batch__item__id"]
            merged_inventory[item_id]["stock__batch__item__id"] = item_id
            merged_inventory[item_id]["stock__batch__item__name"] = inv[
                "stock__batch__item__name"
            ]
            merged_inventory[item_id]["stock__quantity"] = inv["stock__quantity"]
            merged_inventory[item_id]["total_facturation"] = inv["total_facturation"]
            merged_inventory[item_id]["total"] = inv["total_facturation"]

        # Extend the inventory with item that has never been facturationd before
        items = order_models.Item.objects.filter(
            organization=self.request.organization
        ).exclude(id__in=merged_inventory.keys())

        # Sorting by item name
        for item in items:
            merged_inventory[item.id]["stock__batch__item__id"] = item.id
            merged_inventory[item.id]["stock__batch__item__name"] = item.name
            merged_inventory[item.id]["stock__quantity"] = item.quantity
        inventory_list = list(merged_inventory.values())
        context["inventories"] = inventory_list
        sale_inventory_bar_plot, sale_inventory_bar_script = (
            report_plots.sale_inventory_bar_plot(inventory_list)
        )
        context["sale_inventory_bar_plot"] = sale_inventory_bar_plot
        context["sale_inventory_bar_script"] = sale_inventory_bar_script

        context["filter"] = order_filter
        context["cashflow_reports"] = {
            "facturations": {
                "facturation_reports": facturation_reports,
                "total": mixed_total_facturations,
                "total_price": mixed_total_facturation_price,
            },
            "transactions": [
                {
                    "name": "Encaissements",
                    "total": total_deposits,
                    "total_amount": total_deposit_amount,
                },
                {
                    "name": "Décaissements",
                    "total": total_withdrawals,
                    "total_amount": total_withdrawal_amount,
                },
            ],
            "balance": Decimal(total_deposit_amount) - Decimal(total_withdrawal_amount),
            "global_balance": global_balance,
        }

        return context

    def get_template_names(self):
        if self.request.htmx:
            print("this is a htmx request by liedjify")
            return ["reports/org_report.html#report_content"]
        return ["reports/org_report.html"]


class OrgFacturationDetailedReportView(
    LoginRequiredMixin,
    # MembershipRequiredMixin,
    # AdminRequiredMixin,
    TemplateView,
):
    template_name = "orders/commercial_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        withdrawals = cashflow_models.Withdrawal.objects.for_organization(
            organization=self.request.organization
        ).all()
        deposits = cashflow_models.Deposit.objects.for_organization(
            organization=self.request.organization
        ).all()

        facturations = order_models.Facturation.objects.filter(
            organization=self.request.organization
        ).all()

        facturation_filter = BaseFilter(self.request.GET, queryset=facturations)

        deposit_filter = BaseFilter(self.request.GET, queryset=deposits)
        withdrawal_filter = BaseFilter(self.request.GET, queryset=withdrawals)

        total_deposits = deposit_filter.qs.count()
        total_withdrawals = withdrawal_filter.qs.count()

        total_deposit_amount = (
            deposit_filter.qs.aggregate(total_amount=Sum("amount"))["total_amount"]
            or 0.0
        )

        total_withdrawal_amount = (
            withdrawal_filter.qs.aggregate(total_amount=Sum("amount"))["total_amount"]
            or 0.0
        )

        total_facturations = facturation_filter.qs.count() or 0

        total_facturation_price = (
            facturation_filter.qs.aggregate(
                total_price=Sum(F("s__unit_price") * F("s__quantity"))
            )["total_price"]
            or 0.0
        )

        mixed_total_facturation_price = Decimal(total_facturation_price)

        facturation_reports = []
        facturation_reports.append(
            {
                "type": "Vente de produits en espèces",
                "total": total_facturations,
                "total_price": total_facturation_price,
            }
        )

        order_filter = BaseOrganizationFilter(
            self.request.GET,
            queryset=order_models.Facturation.objects.filter(
                organization__in=self.request.organization.get_descendants(
                    include_self=True
                )
            ),
        )

        global_deposit = (
            cashflow_models.Deposit.objects.aggregate(total_amount=Sum("amount"))[
                "total_amount"
            ]
            or 0.0
        )

        global_withdrawal = (
            cashflow_models.Withdrawal.objects.aggregate(total_amount=Sum("amount"))[
                "total_amount"
            ]
            or 0.0
        )

        global_balance = Decimal(global_deposit) - Decimal(global_withdrawal)

        context["filter"] = order_filter

        context["facturations"] = facturations

        context["cashflow_reports"] = {
            "facturations": {
                "facturation_reports": facturation_reports,
                "total_price": mixed_total_facturation_price,
            },
            "transactions": [
                {
                    "name": "Encaissements",
                    "total": total_deposits,
                    "total_amount": total_deposit_amount,
                },
                {
                    "name": "Décaissements",
                    "total": total_withdrawals,
                    "total_amount": total_withdrawal_amount,
                },
            ],
            "balance": Decimal(total_deposit_amount) - Decimal(total_withdrawal_amount),
            "global_balance": global_balance,
        }

        return context

    def get_template_names(self):
        if self.request.htmx:
            print("this is a htmx request by liedjify")
            return ["reports/org_facturation_detailed_report.html#report_content"]
        return ["reports/org_facturation_detailed_report.html"]


class OrgReportPrintView(OrgReportView):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return services.render_pdf(
            request,
            "reports/org_report_print.html",
            context=context,
            output_filename="état-de-sante-de-l'entreprise",
        )


class OrgFacturationGlobalReportView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    TemplateView,
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        organizations = Organization.objects.active_for_user(user=self.request.user)

        context["organizations"] = organizations
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, "reports/report.html", context)


class OrgPrintFacturationGlobalReportView(OrgFacturationGlobalReportView):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return services.render_pdf(
            request,
            "reports/report_print.html",
            context=context,
            output_filename="état-de-sante-de-l'entreprise",
        )
