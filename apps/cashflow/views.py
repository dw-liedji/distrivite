from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django_filters.views import FilterView
from apps.cashflow.filters import TransactionFilter, DepositFilter, WithdrawalFilter
from decimal import Decimal
from apps.core import decorators as core_decorators
from apps.cashflow import forms, models
from apps.core import services
from apps.organization.mixins import (
    ActiveSubscriptionRequiredMixin,
    AdminRequiredMixin,
    MembershipRequiredMixin,
    OrgFormMixin,
    OrgOnlyFormMixin,
)


class OrgCashRegisterListView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    ListView,
):
    model = models.CashRegister
    template_name = "cashflow/cash_register_list.html"
    context_object_name = "cash_registers"
    paginate_by = 20

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["cashflow/cash_register_list.html#list"]
            return ["cashflow/cash_register_list.html#list"]
        return ["cashflow/cash_register_list.html"]

    def get_queryset(self):
        return (
            models.CashRegister.objects.for_organization(
                organization=self.request.organization
            )
            # .prefetch_related("transactions")
            .all()
        )


class OrgCashRegisterCreateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    CreateView,
):
    model = models.CashRegister
    form_class = forms.CashRegisterForm
    template_name = "cashflow/cash_register_add.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/cash_register_add.html#add"]
        return ["cashflow/cash_register_add.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:cash_register_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgCashRegisterUpdateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    UpdateView,
):
    model = models.CashRegister
    form_class = forms.CashRegisterForm
    template_name = "cashflow/cash_register_edit.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/cash_register_change.html#change"]
        return ["cashflow/cash_register_change.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:cash_register_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgCashRegisterDetailView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.CashRegister
    template_name = "cashflow/cash_register_detail.html"
    context_object_name = "cash_register"

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/cash_register_detail.html#detail"]
        return ["cashflow/cash_register_detail.html"]


class OrgCashRegisterDeleteView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.CashRegister
    template_name = "cashflow/cash_register_confirm_delete.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get("HX-Request"):
            try:
                self.object.delete()
                messages.success(self.request, f"{self.object} deleted successfully")
                return HttpResponseRedirect(self.get_success_url())
            except ProtectedError as e:
                related_objects = e.protected_objects  # This is already a set
                related_model_names = {
                    rel._meta.verbose_name for rel in related_objects
                }

                if related_model_names:
                    messages.error(
                        request,
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to existing: {', '.join(related_model_names)} records.",
                    )
                else:
                    messages.error(
                        request,
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to other records.",
                    )
                return HttpResponseRedirect(self.get_success_url())
            except Exception:
                messages.error(
                    request, "An unexpected error occurred. Please try again later."
                )
                return HttpResponseRedirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:cash_register_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgCategoryListView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    ActiveSubscriptionRequiredMixin,
    # AdminRequiredMixin,
    ListView,
):
    model = models.Category
    template_name = "cashflow/category_list.html"
    context_object_name = "categories"
    paginate_by = 20

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["cashflow/category_list.html#list"]
            return ["cashflow/category_list.html#list"]
        return ["cashflow/category_list.html"]

    def get_queryset(self):
        return (
            models.Category.objects.for_organization(
                organization=self.request.organization
            )
            .order_by("-created")
            .all()
        )


class OrgCategoryAddView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    ActiveSubscriptionRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    CreateView,
):
    model = models.Category
    form_class = forms.CategoryForm
    template_name = "cashflow/category_add.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/category_add.html#add"]
        return ["cashflow/category_add.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:category_list",
            kwargs={"organization": self.request.organization.slug},
        )

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())


class OrgCategoryChangeView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    ActiveSubscriptionRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    UpdateView,
):
    model = models.Category
    form_class = forms.CategoryForm
    template_name = "cashflow/category_change.html"

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/category_change.html#change"]
        return ["cashflow/category_change.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:category_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgCategoryDetailView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    ActiveSubscriptionRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Category
    context_object_name = "category"
    template_name = "cashflow/category_detail.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/category_detail.html#detail"]
        return ["cashflow/category_detail.html"]


class OrgCategoryDeleteView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    ActiveSubscriptionRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.Category
    template_name = "cashflow/category_delete.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get("HX-Request"):
            try:
                self.object.delete()
                messages.success(self.request, f"{self.object} deleted successfully")
                return HttpResponseRedirect(self.get_success_url())
            except ProtectedError as e:
                related_objects = e.protected_objects  # This is already a set
                related_model_names = {
                    rel._meta.verbose_name for rel in related_objects
                }

                if related_model_names:
                    messages.error(
                        request,
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to existing: {', '.join(related_model_names)} records.",
                    )
                else:
                    messages.error(
                        request,
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to other records.",
                    )
                return HttpResponseRedirect(self.get_success_url())
            except Exception:
                messages.error(
                    request, "An unexpected error occurred. Please try again later."
                )
                return HttpResponseRedirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:category_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgExpenseReceiptView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Withdrawal
    context_object_name = "withdrawal"
    template_name = "cashflow/withdrawal_receipt.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return services.render_pdf(
            request,
            self.template_name,
            context=self.get_context_data(),
            output_filename=f"{self.object.recipient.split(' ')[0]}-expense-receipt",
        )


class OrgDepositReceiptView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Deposit
    context_object_name = "deposit"
    template_name = "cashflow/deposit_receipt.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return services.render_pdf(
            request,
            self.template_name,
            context=self.get_context_data(),
            output_filename=f"{self.object.organization_user.user.username.split(' ')[0]}-deposit-receipt",
        )


class OrgDepositListView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    FilterView,
):
    model = models.Deposit
    template_name = "cashflow/deposit_list.html"
    context_object_name = "deposits"
    filterset_class = DepositFilter
    paginate_by = 20

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["cashflow/deposit_list.html#list"]
            return ["cashflow/deposit_list.html#list"]
        return ["cashflow/deposit_list.html"]

    def get_queryset(self):
        return (
            models.Deposit.objects.for_organization(
                organization=self.request.organization
            )
            .select_related("organization_user__user", "cash_register")
            .order_by("-created")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrgDepositCreateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    CreateView,
):
    model = models.Deposit
    form_class = forms.DepositForm
    template_name = "cashflow/deposit_add.html"
    success_message = "deposits %(name)s successfully creatsed!"

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/deposit_add.html#add"]
        return ["cashflow/deposit_add.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:deposit_list",
            kwargs={"organization": self.request.organization.slug},
        )

    def get_form_kwargs(self):
        kwargs = super(OrgDepositCreateView, self).get_form_kwargs()

        kwargs.update(
            {
                "organization": self.request.organization,
                "organization_user": self.request.organization_user,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrgDepositUpdateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    UpdateView,
):
    model = models.Deposit
    form_class = forms.DepositForm
    template_name = "cashflow/deposit_change.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/deposit_change.html#change"]
        return ["cashflow/deposit_change.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:deposit_list",
            kwargs={"organization": self.request.organization.slug},
        )

    def get_form_kwargs(self):
        kwargs = super(OrgDepositUpdateView, self).get_form_kwargs()
        kwargs.update(
            {
                "organization": self.request.organization,
                "organization_user": self.request.organization_user,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrgDepositDetailView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Deposit
    context_object_name = "deposit"
    template_name = "cashflow/deposit_detail.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/deposit_detail.html#detail"]
        return ["cashflow/deposit_detail.html"]

    def get_object(self, queryset=None):
        self.object = get_object_or_404(models.Deposit, pk=self.kwargs.get("pk"))
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrgDepositDeleteView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.Deposit
    template_name = "cashflow/deposit_confirm_delete.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get("HX-Request"):
            try:
                self.object.delete()
                messages.success(self.request, f"{self.object} deleted successfully")
                return HttpResponseRedirect(self.get_success_url())
            except ProtectedError as e:
                related_objects = e.protected_objects  # This is already a set
                related_model_names = {
                    rel._meta.verbose_name for rel in related_objects
                }

                if related_model_names:
                    messages.error(
                        request,
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to existing: {', '.join(related_model_names)} records.",
                    )
                else:
                    messages.error(
                        request,
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to other records.",
                    )
                return HttpResponseRedirect(self.get_success_url())
            except Exception:
                messages.error(
                    request, "An unexpected error occurred. Please try again later."
                )
                return HttpResponseRedirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:deposit_list",
            kwargs={"organization": self.request.organization.slug},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrgWithdrawalListView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    FilterView,
):
    model = models.Withdrawal
    template_name = "cashflow/withdrawal_list.html"
    context_object_name = "withdrawals"
    filterset_class = WithdrawalFilter
    paginate_by = 20

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["cashflow/withdrawal_list.html#list"]
            return ["cashflow/withdrawal_list.html#list"]
        return ["cashflow/withdrawal_list.html"]

    def get_queryset(self):

        return (
            models.Withdrawal.objects.for_organization(
                organization=self.request.organization
            )
            .select_related("organization_user__user", "cash_register")
            .order_by("-created")
        )


class OrgWithdrawalCreateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    CreateView,
):
    model = models.Withdrawal
    form_class = forms.WithdrawalForm
    template_name = "cashflow/withdrawal_add.html"
    success_message = "withdrawals %(name)s successfully created!"

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/withdrawal_add.html#add"]
        return ["cashflow/withdrawal_add.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:withdrawal_list",
            kwargs={"organization": self.request.organization.slug},
        )

    def get_form_kwargs(self):
        kwargs = super(OrgWithdrawalCreateView, self).get_form_kwargs()

        kwargs.update(
            {
                "organization": self.request.organization,
                "organization_user": self.request.organization_user,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrgWithdrawalUpdateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    UpdateView,
):
    model = models.Withdrawal
    form_class = forms.WithdrawalForm
    template_name = "cashflow/withdrawal_edit.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["cashflow/withdrawal_change.html#change"]
        return ["cashflow/withdrawal_change.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:withdrawal_list",
            kwargs={"organization": self.request.organization.slug},
        )

    def get_form_kwargs(self):
        kwargs = super(OrgWithdrawalUpdateView, self).get_form_kwargs()

        kwargs.update(
            {
                "organization": self.request.organization,
                "organization_user": self.request.organization_user,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrgWithdrawalDetailView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Withdrawal
    context_object_name = "withdrawal"
    template_name = "cashflow/withdrawal_detail.html"

    def get_object(self, queryset=None):
        self.object = get_object_or_404(models.Withdrawal, pk=self.kwargs.get("pk"))
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrgWithdrawalDeleteView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.Withdrawal
    template_name = "cashflow/withdrawal_confirm_delete.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get("HX-Request"):
            try:
                self.object.delete()
                messages.success(self.request, f"{self.object} deleted successfully")
                return HttpResponseRedirect(self.get_success_url())
            except ProtectedError as e:
                related_objects = e.protected_objects  # This is already a set
                related_model_names = {
                    rel._meta.verbose_name for rel in related_objects
                }

                if related_model_names:
                    messages.error(
                        request,
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to existing: {', '.join(related_model_names)} records.",
                    )
                else:
                    messages.error(
                        request,
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to other records.",
                    )
                return HttpResponseRedirect(self.get_success_url())
            except Exception:
                messages.error(
                    request, "An unexpected error occurred. Please try again later."
                )
                return HttpResponseRedirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:cashflow:withdrawal_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgWithdrawalFinishedView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Withdrawal
    context_object_name = "withdrawal"
    template_name = "cashflow/withdrawal_detail.html"

    def get(self, request, *args, **kwargs):
        withdrawal = self.get_object()

        # Update delivery state of the facturation
        withdrawal.is_validated = True
        withdrawal.save()

        messages.success(request, "Validated successfully.")

        return HttpResponseRedirect(
            reverse_lazy(
                "organization_features:cashflow:withdrawal_list",
                kwargs={
                    "organization": self.request.organization.slug,
                },
            )
        )


class OrgTransactionListView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    FilterView,
):
    model = models.Transaction
    template_name = "cashflow/transaction_list.html"
    context_object_name = "transactions"
    filterset_class = TransactionFilter

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["cashflow/transaction_list.html#list"]
            return ["cashflow/transaction_list.html#list"]
        return ["cashflow/transaction_list.html"]

    def get_queryset(self):
        return (
            models.Transaction.objects.for_organization(
                organization=self.request.organization
            )
            .select_related("organization_user__user", "cash_register")
            .order_by("-created")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrgPrintWithdrawalListView(OrgWithdrawalListView):
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filtered_queryset = self.filterset_class(request.GET, queryset=queryset).qs

        context = {
            "filter": self.filterset_class(request.GET, queryset=queryset),
            "filtered_transactions": filtered_queryset,
            "total_amount": filtered_queryset.aggregate(total_amount=Sum("amount"))[
                "total_amount"
            ],
            "total_transactions": len(filtered_queryset),
        }

        return services.render_pdf(
            request,
            "cashflow/report_expense.html",
            context=context,
            output_filename="rapport-caisse-depenses",
        )
        # return render(request, "orders/report.html", context)  # preview


class OrgPrintDepositListView(OrgDepositListView):
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filtered_queryset = self.filterset_class(request.GET, queryset=queryset).qs

        context = {
            "filter": self.filterset_class(request.GET, queryset=queryset),
            "filtered_transactions": filtered_queryset,
            "total_amount": filtered_queryset.aggregate(total_amount=Sum("amount"))[
                "total_amount"
            ],
            "total_transactions": len(filtered_queryset),
        }

        return services.render_pdf(
            request,
            "cashflow/report_deposit.html",
            context=context,
            output_filename="rapport-caisse-recette",
        )
        # return render(request, "orders/report.html", context)  # preview


class OrgPrintTransactionListView(OrgTransactionListView):
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        transaction_filter = self.filterset_class(request.GET, queryset=queryset)
        filtered_queryset = transaction_filter.qs

        withdrawals = models.Withdrawal.objects.for_organization(
            organization=self.request.organization
        ).all()

        deposits = models.Deposit.objects.for_organization(
            organization=self.request.organization
        ).all()

        deposit_filter = self.filterset_class(self.request.GET, queryset=deposits)
        withdrawal_filter = self.filterset_class(self.request.GET, queryset=withdrawals)

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

        global_total_deposit_amount = (
            deposits.aggregate(total_amount=Sum("amount"))["total_amount"] or 0.0
        )
        global_total_withdrawal_amount = (
            withdrawals.aggregate(total_amount=Sum("amount"))["total_amount"] or 0.0
        )

        filter_form = transaction_filter.form
        filter_form_data_list = []
        if filter_form.is_valid():
            for field_name, field_value in filter_form.cleaned_data.items():
                field_label = filter_form.fields[field_name].label

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

        context = {
            "filter_form_data": filter_form_data_list,
            "filter": self.filterset_class(request.GET, queryset=queryset),
            "filtered_transactions": filtered_queryset,
            "total_amount": filtered_queryset.aggregate(total_amount=Sum("amount"))[
                "total_amount"
            ],
            "total_transactions": len(filtered_queryset),
            "report_decaissement": {
                "total": total_withdrawals,
                "total_amount": total_withdrawal_amount,
                "global_total_amount": global_total_withdrawal_amount,
            },
            "report_encaissement": {
                "total": total_deposits,
                "total_amount": total_deposit_amount,
                "global_total_amount": global_total_deposit_amount,
            },
            "balance": Decimal(total_deposit_amount) - Decimal(total_withdrawal_amount),
            "global_balance": Decimal(global_total_deposit_amount)
            - Decimal(global_total_withdrawal_amount),
        }

        return services.render_pdf(
            request,
            "cashflow/report_transaction.html",
            context=context,
            output_filename="rapport-mouvement-caisse",
        )
        # return render(request, "orders/report.html", context)  # preview
