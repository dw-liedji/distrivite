# reports/views.py

from decimal import Decimal

from django.db.models import Count, F, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cashflow import models as cashflow_models
from apps.cashflow.models import Deposit, Withdrawal
from apps.core.filters import BaseFilter
from apps.orders import models as order_models
from apps.orders.filters import BaseFilter


class OrgSaleReportAPI(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        organization = request.organization
        app = "distrivite"

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
                    F("facturation_batchs__unit_price")
                    * F("facturation_batchs__quantity")
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
        facturation_batchs = order_models.FacturationBatch.objects.filter(
            organization=self.request.organization
        )

        return Response(
            {
                "cash_sales_application": app,
                "cash_sales_organization": str(organization),
                "cash_sales_type": "CashSale",
                "cash_sales_name": "Vente de produits en espèces",
                "cash_sales_total": total_facturations,
                "cash_sales_total_amount": total_facturation_price,
                "coverage_sales_application": app,
                "coverage_sales_organization": organization.name,
                "coverage_sales_type": "CoverageSale",
                "coverage_sales_name": "Vente de produits à termes (Accepted)",
                "coverage_sales_total": 0,
                "coverage_sales_total_amount": 0.0,
                "coverage_complements_application": app,
                "coverage_complements_organization": organization.name,
                "coverage_complements_type": "CoverageComplementSale",
                "coverage_complements_name": "Complement de produits vente à termes (Accepted)",
                "coverage_complements_total": 0,
                "coverage_complements_total_amount": 0.0,
                "service_sales_application": app,
                "service_sales_organization": organization.name,
                "service_sales_type": "CombinedSale",
                "service_sales_name": "Total ventes",
                "service_sales_total": 0,
                "service_sales_total_amount": 0.0,
                # "combined_sales_total": combined_sales_total,
                # "combined_sales_total_amount": float(combined_sales_total_amount),
                # "cashflow_withdrawals_total": total_withdrawals,
                # "cashflow_withdrawals_amount": total_withdrawal_amount,
                # "cashflow_deposits_total": total_deposits,
                # "cashflow_deposits_amount": total_deposit_amount,
            }
        )


class CashflowReportAPI(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        org = request.organization
        app_name = "distrivite"

        # Get all deposits and withdrawals for this organization
        deposits = cashflow_models.Deposit.objects.for_organization(
            organization=org
        ).all()
        withdrawals = cashflow_models.Withdrawal.objects.for_organization(
            organization=org
        ).all()

        # Apply filters (if needed)
        deposit_filter = BaseFilter(request.GET, queryset=deposits)
        withdrawal_filter = BaseFilter(request.GET, queryset=withdrawals)

        # Totals and amounts
        deposit_total = deposit_filter.qs.count()
        withdrawal_total = withdrawal_filter.qs.count()

        deposit_amount = deposit_filter.qs.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.0")

        withdrawal_amount = withdrawal_filter.qs.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.0")

        # Balance = inflow - outflow
        balance = Decimal(deposit_amount) - Decimal(withdrawal_amount)

        # Global balance (no filters applied)
        global_deposit = cashflow_models.Deposit.objects.filter(
            organization=org
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.0")

        global_withdrawal = cashflow_models.Withdrawal.objects.filter(
            organization=org
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.0")

        global_balance = Decimal(global_deposit) - Decimal(global_withdrawal)

        return Response(
            {
                "cashflow_application": app_name,
                "cashflow_organization": str(org),
                "cashflow_type": "Trésorerie",
                "cashflow_name": "Mouvements de trésorerie",
                "cashflow_total": deposit_total + withdrawal_total,
                "cashflow_total_amount": deposit_amount + withdrawal_amount,
                "cashflow_inflow_name": "Entrées de trésorerie",
                "cashflow_inflow_total": deposit_total,
                "cashflow_inflow_amount": deposit_amount,
                "cashflow_outflow_name": "Sorties de trésorerie",
                "cashflow_outflow_total": withdrawal_total,
                "cashflow_outflow_amount": withdrawal_amount,
                "cashflow_balance": balance,
                "cashflow_global_balance": global_balance,
            }
        )
