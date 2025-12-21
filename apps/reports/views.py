from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    F,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.views.generic import TemplateView

from apps.core import services
from apps.core.filters import BaseFilter
from apps.orders import models as order_models
from apps.orders.filters import BaseOrganizationFilter
from apps.organization.mixins import (
    MembershipRequiredMixin,
)
from apps.organization.models import Organization
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

        facturations = order_models.Facturation.objects.filter(
            organization=self.request.organization
        ).all()

        facturation_filter = BaseFilter(self.request.GET, queryset=facturations)

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
                    "total": 0,
                    "total_amount": 0,
                },
                {
                    "name": "Décaissements",
                    "total": 0,
                    "total_amount": 0,
                },
            ],
            "balance": Decimal(0) - Decimal(0),
            "global_balance": 0,
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

        facturations = order_models.Facturation.objects.filter(
            organization=self.request.organization
        ).all()

        facturation_filter = BaseFilter(self.request.GET, queryset=facturations)
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
                    "total": 0,
                    "total_amount": 0,
                },
                {
                    "name": "Décaissements",
                    "total": 0,
                    "total_amount": 0,
                },
            ],
            "balance": Decimal(0) - Decimal(0),
            "global_balance": 0,
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
