from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import (
    Case,
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    ProtectedError,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django_filters.views import FilterView
from django_htmx.http import push_url, replace_url

from apps.core import decorators as core_decorators
from apps.core import services
from apps.orders import filters as orders_filters
from apps.orders import forms, models
from apps.organization import mixins

from . import resources


class OrgCustomerListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    FilterView,
):
    model = models.Customer
    template_name = "orders/patient_list.html"
    context_object_name = "patients"
    paginate_by = 30
    permission_required = ("orders.view_patient",)
    filterset_class = orders_filters.CustomerFilter

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/patient_list.html#list"]
            return ["orders/patient_list.html#list"]
        return ["orders/patient_list.html"]

    def get_queryset(self):
        organization = self.request.organization

        # Subquery for total sales
        total_sales_subquery = (
            models.Facturation.objects.filter(
                organization=organization, customer_id=OuterRef("pk"), is_proforma=False
            )
            .values("customer_id")
            .annotate(
                total=Coalesce(
                    Sum(
                        F("facturation_stocks__unit_price")
                        * F("facturation_stocks__quantity"),
                        output_field=DecimalField(max_digits=19, decimal_places=4),
                    ),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=19, decimal_places=4),
                )
            )
            .values("total")[:1]
        )

        # Subquery for total paid
        total_paid_subquery = (
            models.FacturationPayment.objects.filter(
                organization=organization, facturation__customer_id=OuterRef("pk")
            )
            .values("facturation__customer_id")
            .annotate(
                total=Coalesce(
                    Sum(
                        "amount",
                        output_field=DecimalField(max_digits=19, decimal_places=4),
                    ),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=19, decimal_places=4),
                )
            )
            .values("total")[:1]
        )

        # Apply annotations
        return (
            models.Customer.objects.filter(organization=organization)
            .annotate(
                total_sales=Coalesce(
                    Subquery(total_sales_subquery),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=19, decimal_places=4),
                ),
                total_paid=Coalesce(
                    Subquery(total_paid_subquery),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=19, decimal_places=4),
                ),
            )
            .annotate(
                total_due=Coalesce(
                    F("total_sales") - F("total_paid"),
                    Decimal("0"),
                    output_field=DecimalField(max_digits=19, decimal_places=4),
                ),
                # Payment progress percentage (how much of total sales is paid)
                payment_progress=Case(
                    When(
                        total_sales__gt=0,
                        then=ExpressionWrapper(
                            (F("total_paid") * 100) / F("total_sales"),
                            output_field=DecimalField(max_digits=5, decimal_places=1),
                        ),
                    ),
                    default=Value(100),
                    output_field=DecimalField(max_digits=5, decimal_places=1),
                ),
                # Credit utilization percentage (how much of credit limit is used)
                credit_utilization=Case(
                    When(
                        credit_limit__gt=0,
                        then=ExpressionWrapper(
                            (F("total_due") * 100) / F("credit_limit"),
                            output_field=DecimalField(max_digits=5, decimal_places=1),
                        ),
                    ),
                    default=Value(0),
                    output_field=DecimalField(max_digits=5, decimal_places=1),
                ),
            )
        )


class OrgCustomerAddView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    CreateView,
):
    model = models.Customer
    form_class = forms.CustomerForm
    template_name = "orders/patient_add.html"
    permission_required = ("orders.add_patient",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/patient_add.html#add"]
        return ["orders/patient_add.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Customer {consultation} saved successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Customer failed to be saved. Somthing went wrong."
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:patient_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgCustomerChangeView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    UpdateView,
):
    model = models.Customer
    form_class = forms.CustomerForm
    template_name = "orders/patient_change.html"
    permission_required = ("orders.change_patient",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/patient_change.html#change"]
        return ["orders/patient_change.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Customer {consultation} updated successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Error updating consultation {self.get_object()}"
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:patient_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgCustomerDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DeleteView,
):
    model = models.Customer
    template_name = "orders/patient_confirm_delete.html"
    permission_required = ("orders.delete_patient",)

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
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:patient_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgCustomerDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DetailView,
):
    model = models.Customer
    context_object_name = "patient"
    template_name = "orders/patient_detail.html"
    permission_required = ("orders.view_patient",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/patient_detail.html#detail"]
        return ["orders/patient_detail.html"]


class OrgBatchListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    FilterView,
):
    model = models.Batch
    template_name = "orders/batch_list.html"
    context_object_name = "batchs"
    filterset_class = orders_filters.BatchFilter
    paginate_by = 30
    permission_required = ("orders.view_batch",)

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/batch_list.html#list"]
            return ["orders/batch_list.html#list"]
        return ["orders/batch_list.html"]

    def get_queryset(self):
        return models.Batch.objects.filter(
            organization__in=self.request.organization.get_descendants(
                include_self=True
            )
        ).order_by("item__name")


class OrgBatchAddView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    CreateView,
):
    model = models.Batch
    form_class = forms.BatchForm
    template_name = "orders/batch_add.html"
    permission_required = ("orders.add_batch",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/batch_add.html#add"]
        return ["orders/batch_add.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Batch {consultation} saved successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Batch failed to be saved. Somthing went wrong."
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:batch_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgBatchChangeView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    UpdateView,
):
    model = models.Batch
    form_class = forms.BatchForm
    template_name = "orders/batch_change.html"
    permission_required = ("orders.change_batch",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/batch_change.html#change"]
        return ["orders/batch_change.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Batch {consultation} updated successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Error updating consultation {self.get_object()}"
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:batch_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgBatchDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DeleteView,
):
    model = models.Batch
    template_name = "orders/batch_confirm_delete.html"
    permission_required = ("orders.delete_batch",)

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
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:batch_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgBatchDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DetailView,
):
    model = models.Batch
    context_object_name = "batch"
    template_name = "orders/batch_detail.html"
    permission_required = ("orders.view_batch",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/batch_detail.html#detail"]
        return ["orders/batch_detail.html"]


class OrgStockListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    FilterView,
):
    model = models.Stock
    template_name = "orders/stock_list.html"
    context_object_name = "stocks"
    filterset_class = orders_filters.StockFilter
    paginate_by = 30
    permission_required = ("orders.view_stock",)

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/stock_list.html#list"]
            return ["orders/stock_list.html#list"]
        return ["orders/stock_list.html"]

    def get_queryset(self):
        return models.Stock.objects.filter(
            organization=self.request.organization
        ).order_by("batch__item__name")


class OrgStockAddView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    CreateView,
):
    model = models.Stock
    form_class = forms.StockForm
    template_name = "orders/stock_add.html"
    permission_required = ("orders.add_stock",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/stock_add.html#add"]
        return ["orders/stock_add.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Stock {consultation} saved successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Stock failed to be saved. Somthing went wrong."
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:stock_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgStockChangeView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    UpdateView,
):
    model = models.Stock
    form_class = forms.StockForm
    template_name = "orders/stock_change.html"
    permission_required = ("orders.change_stock",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/stock_change.html#change"]
        return ["orders/stock_change.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Stock {consultation} updated successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Error updating consultation {self.get_object()}"
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:stock_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgStockDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DeleteView,
):
    model = models.Stock
    template_name = "orders/stock_confirm_delete.html"
    permission_required = ("orders.delete_stock",)

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
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:stock_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgStockDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DetailView,
):
    model = models.Stock
    context_object_name = "stock"
    template_name = "orders/stock_detail.html"
    permission_required = ("orders.view_stock",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/stock_detail.html#detail"]
        return ["orders/stock_detail.html"]


class OrgItemListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    FilterView,
):
    model = models.Item
    template_name = "orders/item_list.html"
    context_object_name = "items"
    filterset_class = orders_filters.ItemFilter
    paginate_by = 30
    permission_required = ("orders.view_item",)

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/item_list.html#list"]
            return ["orders/item_list.html#list"]
        return ["orders/item_list.html"]

    def get_queryset(self):
        return models.Item.objects.filter(
            organization__in=self.request.organization.get_descendants(
                include_self=True
            )
        ).order_by("name")


class OrgItemAddView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    CreateView,
):
    model = models.Item
    form_class = forms.ItemForm
    template_name = "orders/item_add.html"
    permission_required = ("orders.add_item",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/item_add.html#add"]
        return ["orders/item_add.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Item {consultation} saved successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(self.request, f"Item failed to be saved. Somthing went wrong.")
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:item_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgItemChangeView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    UpdateView,
):
    model = models.Item
    form_class = forms.ItemForm
    template_name = "orders/item_change.html"
    permission_required = ("orders.change_item",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/item_change.html#change"]
        return ["orders/item_change.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Item {consultation} updated successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Error updating consultation {self.get_object()}"
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:item_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgItemDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DeleteView,
):
    model = models.Item
    template_name = "orders/item_confirm_delete.html"
    permission_required = ("orders.delete_item",)

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
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:item_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgItemDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DetailView,
):
    model = models.Item
    context_object_name = "item"
    template_name = "orders/item_detail.html"
    permission_required = ("orders.view_item",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/item_detail.html#detail"]
        return ["orders/item_detail.html"]


class OrgSupplierListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    FilterView,
):
    model = models.Supplier
    template_name = "orders/supplier_list.html"
    context_object_name = "suppliers"
    paginate_by = 30
    permission_required = ("orders.view_supplier",)
    filterset_class = orders_filters.SupplierFilter

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/supplier_list.html#list"]
            return ["orders/supplier_list.html#list"]
        return ["orders/supplier_list.html"]

    def get_queryset(self):
        return models.Supplier.objects.filter(
            organization__in=self.request.organization.get_descendants(
                include_self=True
            )
        ).order_by("-created")


class OrgSupplierAddView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    CreateView,
):
    model = models.Supplier
    form_class = forms.SupplierForm
    template_name = "orders/supplier_add.html"
    permission_required = ("orders.add_supplier",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/supplier_add.html#add"]
        return ["orders/supplier_add.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Supplier {consultation} saved successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Supplier failed to be saved. Somthing went wrong."
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:supplier_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgSupplierChangeView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    UpdateView,
):
    model = models.Supplier
    form_class = forms.SupplierForm
    template_name = "orders/supplier_change.html"
    permission_required = ("orders.change_supplier",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/supplier_change.html#change"]
        return ["orders/supplier_change.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Supplier {consultation} updated successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Error updating consultation {self.get_object()}"
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:supplier_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgSupplierDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DeleteView,
):
    model = models.Supplier
    template_name = "orders/supplier_confirm_delete.html"
    permission_required = ("orders.delete_supplier",)

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
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:supplier_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgSupplierDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DetailView,
):
    model = models.Supplier
    context_object_name = "supplier"
    template_name = "orders/supplier_detail.html"
    permission_required = ("orders.view_supplier",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/supplier_detail.html#detail"]
        return ["orders/supplier_detail.html"]


class OrgCategoryListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    FilterView,
):
    model = models.Category
    template_name = "orders/category_list.html"
    context_object_name = "categories"
    paginate_by = 30
    permission_required = ("orders.view_category",)
    filterset_class = orders_filters.CategoryFilter

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/category_list.html#list"]
            return ["orders/category_list.html#list"]
        return ["orders/category_list.html"]

    def get_queryset(self):
        return models.Category.objects.filter(
            organization__in=self.request.organization.get_descendants(
                include_self=True
            )
        ).order_by("-created")

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        if self.request.htmx:
            return replace_url(
                response, self.request.get_full_path()
            )  # Push updated URL
        return response


class OrgCategoryAddView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    CreateView,
):
    model = models.Category
    form_class = forms.CategoryForm
    template_name = "orders/category_add.html"
    permission_required = ("orders.add_category",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/category_add.html#add"]
        return ["orders/category_add.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Category {consultation} saved successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Category failed to be saved. Somthing went wrong."
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:category_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgCategoryChangeView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    UpdateView,
):
    model = models.Category
    form_class = forms.CategoryForm
    template_name = "orders/category_change.html"
    permission_required = ("orders.change_category",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/category_change.html#change"]
        return ["orders/category_change.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(self.request, f"Category {consultation} updated successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Error updating consultation {self.get_object()}"
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:category_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgCategoryDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DeleteView,
):
    model = models.Category
    template_name = "orders/category_confirm_delete.html"
    permission_required = ("orders.delete_category",)

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
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:category_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgCategoryDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DetailView,
):
    model = models.Category
    context_object_name = "category"
    template_name = "orders/category_detail.html"
    permission_required = ("orders.view_category",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/category_detail.html#detail"]
        return ["orders/category_detail.html"]


class OrgFacturationListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    FilterView,
):
    model = models.Facturation
    template_name = "orders/facturation_list.html"
    context_object_name = "facturations"
    paginate_by = 30
    permission_required = ("orders.view_facturation",)
    filterset_class = orders_filters.FacturationFilter

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/facturation_list.html#list"]
            return ["orders/facturation_list.html#list"]
        return ["orders/facturation_list.html"]

    def get_queryset(self):
        return models.Facturation.objects.filter(
            organization=self.request.organization
        ).order_by("-created")


class OrgFacturationAddView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    CreateView,
):
    model = models.Facturation
    form_class = forms.FacturationForm
    template_name = "orders/facturation_add.html"
    permission_required = ("orders.add_facturation",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_add.html#add"]
        return ["orders/facturation_add.html"]

    def form_valid(self, form):
        print("foloiwng errors ", form.errors)
        consultation = form.save()
        messages.success(self.request, f"Facturation {consultation} saved successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Facturation failed to be saved. Somthing went wrong."
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:facturation_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgFacturationChangeView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    UpdateView,
):
    model = models.Facturation
    form_class = forms.FacturationForm
    template_name = "orders/facturation_change.html"
    permission_required = ("orders.change_facturation",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_change.html#change"]
        return ["orders/facturation_change.html"]

    def form_valid(self, form):
        consultation = form.save()
        messages.success(
            self.request, f"Facturation {consultation} updated successfully"
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.success(
            self.request, f"Error updating consultation {self.get_object()}"
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:facturation_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgFacturationDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DeleteView,
):
    model = models.Facturation
    template_name = "orders/facturation_confirm_delete.html"
    permission_required = ("orders.delete_facturation",)

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
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:facturation_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgFacturationDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DetailView,
):
    model = models.Facturation
    context_object_name = "facturation"
    template_name = "orders/facturation_detail.html"
    permission_required = ("orders.view_facturation",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_detail.html#detail"]
        return ["orders/facturation_detail.html"]


class OrgFacturationDeliverView(
    LoginRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Facturation
    context_object_name = "facturation"
    template_name = "orders/facturation_detail.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        batchs = self.object.facturation_stocks.all()
        with transaction.atomic():

            # Update delivery state of the facturation
            self.object.is_delivered = True
            self.object.save()

            # Update quantity of each product in stock for each batch in the facturation
            for facturation_stock in batchs:
                stock = facturation_stock.stock
                stock.quantity -= facturation_stock.quantity
                stock.save()
            messages.error(self.request, f"{self.object} delivered successfully")

        if request.headers.get("HX-Request"):
            return HttpResponseRedirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:facturation_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgFacturationApprovedView(
    LoginRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Facturation
    context_object_name = "facturation"
    template_name = "orders/facturation_detail.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Update delivery state of the facturation
        self.object.is_approved = True
        self.object.save()
        messages.error(self.request, f"{self.object} approved successfully")

        if request.headers.get("HX-Request"):
            return HttpResponseRedirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:facturation_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgFacturationReceiptView(
    LoginRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Facturation
    context_object_name = "facturation"
    template_name = "orders/bills/facturation_receipt.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return services.render_pdf(
            request,
            "orders/bills/facturation_receipt.html",
            context=self.get_context_data(),
            output_filename="facturation-receipt",
        )


class OrgFacturationReceiptMatrixPrinterView(
    LoginRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Facturation
    context_object_name = "facturation"
    template_name = "orders/bills/facturation_receipt_matrix_printer.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return services.render_pdf(
            request,
            "orders/bills/facturation_receipt_matrix_printer.html",
            context=self.get_context_data(),
            output_filename="facturation-receipt",
        )


class OrgFacturationProformaView(
    LoginRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.Facturation
    context_object_name = "facturation"
    template_name = "orders/bills/facturation_proforma.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return services.render_pdf(
            request,
            "orders/bills/facturation_proforma.html",
            context=self.get_context_data(),
            output_filename="facturation-proforma",
        )


class OrgFacturationThermalReceiptView(DetailView):
    model = models.Facturation
    context_object_name = "facturation"
    template_name = "orders/bills/facturation_thermal_receipt.html"

    # def get(self, request, *args, **kwargs):
    #     self.object = self.get_object()
    #     return render(request, )


class OrgFacturationStockListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    ListView,
):
    model = models.FacturationStock
    template_name = "orders/facturation_stock_list.html"
    context_object_name = "facturation_stocks"
    facturation = None

    permission_required = ("orders.view_facturationbatch",)

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/facturation_stock_list.html#list"]
            return ["orders/facturation_stock_list.html#list"]
        return ["orders/facturation_stock_list.html"]

    def get_queryset(self):
        self.facturation = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )
        return models.FacturationStock.objects.for_organization(
            organization=self.request.organization
        ).filter(facturation=self.facturation)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = self.facturation
        return context


class OrgFacturationStockCreateView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    mixins.OrgFormMixin,
    CreateView,
):
    model = models.FacturationStock
    form_class = forms.FacturationStockForm
    template_name = "orders/facturation_stock_add.html"
    success_message = "facturation_stocks %(name)s successfully created!"
    facturation = None

    permission_required = ("orders.add_facturationbatch",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_stock_add.html#add"]
        return ["orders/facturation_stock_add.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        if "save" in self.request.POST:
            return reverse_lazy(
                "organization_features:orders:facturation_stock_list",
                kwargs={
                    "organization": self.request.organization.slug,
                    "facturation": self.kwargs.get("facturation"),
                },
            )
        elif "save_continue" in self.request.POST:
            return reverse_lazy(
                "organization_features:orders:facturation_stock_add",
                kwargs={
                    "organization": self.request.organization.slug,
                    "facturation": self.kwargs.get("facturation"),
                },
            )
        else:
            # p Invalid action or form submission
            # ...
            return reverse_lazy(
                "organization_features:orders:facturation_stock_add",
                kwargs={
                    "organization": self.request.organization.slug,
                    "facturation": self.kwargs.get("facturation"),
                },
            )

    def get_form_kwargs(self):
        kwargs = super(OrgFacturationStockCreateView, self).get_form_kwargs()
        self.facturation = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )
        kwargs.update(
            {
                "organization": self.request.organization,
                # "organization_user": self.request.organization_user,
                "facturation": self.facturation,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = self.facturation
        return context


class OrgFacturationStockUpdateView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    mixins.OrgFormMixin,
    UpdateView,
):
    model = models.FacturationStock
    form_class = forms.FacturationStockForm
    template_name = "orders/facturation_stock_edit.html"
    facturation = None
    permission_required = ("orders.change_facturationbatch",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_stock_change.html#change"]
        return ["orders/facturation_stock_change.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:facturation_stock_list",
            kwargs={
                "organization": self.request.organization.slug,
                "facturation": self.kwargs.get("facturation"),
            },
        )

    def get_form_kwargs(self):
        kwargs = super(OrgFacturationStockUpdateView, self).get_form_kwargs()
        self.facturation = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )
        kwargs.update(
            {
                "organization": self.request.organization,
                # "organization_user": self.request.organization_user,
                "facturation": self.facturation,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = self.facturation
        return context


class OrgFacturationStockDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.FacturationStock
    template_name = "orders/facturation_stock_confirm_delete.html"
    permission_required = ("orders.delete_facturationbatch",)

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
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:facturation_stock_list",
            kwargs={
                "organization": self.request.organization.slug,
                "facturation": self.kwargs.get("facturation"),
            },
        )


class OrgFacturationStockDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.FacturationStock
    context_object_name = "facturation_stock"
    template_name = "orders/facturation_stock_detail.html"
    permission_required = ("orders.view_facturationbatch",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_stock_detail.html#detail"]
        return ["orders/facturation_stock_detail.html"]

    def get_object(self, queryset=None):
        self.object = get_object_or_404(
            models.FacturationStock, pk=self.kwargs.get("pk")
        )
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )
        return context


class OrgFacturationPaymentListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    FilterView,
):
    model = models.FacturationPayment
    template_name = "orders/facturation_payment_list.html"
    context_object_name = "facturation_payments"

    permission_required = ("orders.view_facturationpayment",)
    filterset_class = orders_filters.FacturationPaymentFilter
    facturation = None

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/facturation_payment_list.html#list"]
            return ["orders/facturation_payment_list.html#list"]
        return ["orders/facturation_payment_list.html"]

    def get_queryset(self):
        self.facturation = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )

        return models.FacturationPayment.objects.for_organization(
            organization=self.request.organization
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = self.facturation
        return context


class OrgFacturationPaymentCreateView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    mixins.OrgFormMixin,
    mixins.UserFormMixin,
    CreateView,
):
    model = models.FacturationPayment
    form_class = forms.FacturationPaymentForm
    template_name = "orders/facturation_payment_add.html"
    success_message = "facturation_payments %(name)s successfully created!"

    permission_required = ("orders.add_facturationpayment",)
    facturation = None

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_payment_add.html#add"]
        return ["orders/facturation_payment_add.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        if "save" in self.request.POST:
            return reverse_lazy(
                "organization_features:orders:facturation_payment_list",
                kwargs={
                    "organization": self.request.organization.slug,
                    "facturation": self.kwargs.get("facturation"),
                },
            )
        elif "save_continue" in self.request.POST:
            return reverse_lazy(
                "organization_features:orders:facturation_payment_add",
                kwargs={
                    "organization": self.request.organization.slug,
                    "facturation": self.kwargs.get("facturation"),
                },
            )
        else:
            # p Invalid action or form submission
            # ...
            return reverse_lazy(
                "organization_features:orders:facturation_payment_add",
                kwargs={
                    "organization": self.request.organization.slug,
                    "facturation": self.kwargs.get("facturation"),
                },
            )

    def get_form_kwargs(self):
        kwargs = super(OrgFacturationPaymentCreateView, self).get_form_kwargs()
        self.facturation = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )
        kwargs.update(
            {
                "organization": self.request.organization,
                # "organization_user": self.request.organization_user,
                "facturation": self.kwargs.get("facturation"),
            }
        )
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            facturation_payment = form.save(commit=False)
            facturation_payment.payer = self.request.user
            facturation_payment.save()

            if facturation_payment.amount > 0.0:
                cashflow_models.Deposit.objects.create(
                    organization=self.request.organization,
                    organization_user=self.request.organization_user,
                    amount=facturation_payment.amount,
                    operation_date=facturation_payment.operation_date,
                    accounting_date=facturation_payment.accounting_date,
                    cash_register=facturation_payment.cash_register,
                    reason=f"Paiement de {facturation_payment.facturation } par {facturation_payment.payer}",
                )

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = self.facturation
        return context


class OrgFacturationPaymentUpdateView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    mixins.OrgFormMixin,
    mixins.UserFormMixin,
    UpdateView,
):
    model = models.FacturationPayment
    form_class = forms.FacturationPaymentForm
    template_name = "orders/facturation_payment_edit.html"
    permission_required = ("orders.change_facturationpayment",)
    facturation = None

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_payment_change.html#change"]
        return ["orders/facturation_payment_change.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:facturation_payment_list",
            kwargs={
                "organization": self.request.organization.slug,
                "facturation": self.kwargs.get("facturation"),
            },
        )

    def get_form_kwargs(self):
        kwargs = super(OrgFacturationPaymentUpdateView, self).get_form_kwargs()
        self.facturation = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )
        kwargs.update(
            {
                "organization": self.request.organization,
                # "organization_user": self.request.organization_user,
                "facturation": self.kwargs.get("facturation"),
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = self.facturation
        return context


class OrgFacturationPaymentDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.FacturationPayment
    template_name = "orders/facturation_payment_confirm_delete.html"
    permission_required = ("orders.delete_facturationpayment",)

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
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:facturation_payment_list",
            kwargs={
                "organization": self.request.organization.slug,
                "facturation": self.kwargs.get("facturation"),
            },
        )


class OrgFacturationPaymentDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.FacturationPayment
    context_object_name = "facturation_payment"
    template_name = "orders/facturation_payment_detail.html"
    permission_required = ("orders.view_facturationpayment",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_payment_detail.html#detail"]
        return ["orders/facturation_payment_detail.html"]

    def get_object(self, queryset=None):
        self.object = get_object_or_404(
            models.FacturationPayment, pk=self.kwargs.get("pk")
        )
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )
        return context


class OrgFacturationRefundListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    FilterView,
):
    model = models.FacturationRefund
    template_name = "orders/facturation_refund_list.html"
    context_object_name = "facturation_refunds"

    permission_required = ("orders.view_facturationrefund",)
    filterset_class = orders_filters.FacturationRefundFilter
    facturation = None

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/facturation_refund_list.html#list"]
            return ["orders/facturation_refund_list.html#list"]
        return ["orders/facturation_refund_list.html"]

    def get_queryset(self):
        self.facturation = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )

        return models.FacturationRefund.objects.filter(
            organization=self.request.organization, facturation=self.facturation
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = self.facturation
        return context


class OrgFacturationRefundCreateView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    mixins.OrgFormMixin,
    # mixins.UserFormMixin,
    CreateView,
):
    model = models.FacturationRefund
    form_class = forms.FacturationRefundForm
    template_name = "orders/facturation_refund_add.html"
    success_message = "FacturationRefunds %(name)s successfully created!"

    permission_required = ("orders.add_facturationrefund",)
    facturation = None

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_refund_add.html#add"]
        return ["orders/facturation_refund_add.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        if "save" in self.request.POST:
            return reverse_lazy(
                "organization_features:orders:facturation_refund_list",
                kwargs={
                    "organization": self.request.organization.slug,
                    "facturation": self.kwargs.get("facturation"),
                },
            )
        elif "save_continue" in self.request.POST:
            return reverse_lazy(
                "organization_features:orders:facturation_refund_add",
                kwargs={
                    "organization": self.request.organization.slug,
                    "facturation": self.kwargs.get("facturation"),
                },
            )
        else:
            # p Invalid action or form submission
            # ...
            return reverse_lazy(
                "organization_features:orders:facturation_refund_add",
                kwargs={
                    "organization": self.request.organization.slug,
                    "facturation": self.kwargs.get("facturation"),
                },
            )

    def get_form_kwargs(self):
        kwargs = super(OrgFacturationRefundCreateView, self).get_form_kwargs()

        kwargs.update(
            {
                "organization": self.request.organization,
                "organization_user": self.request.organization_user,
                "facturation": self.kwargs.get("facturation"),
            }
        )
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            facturation_refund = form.save(commit=False)
            facturation_refund.reducer = self.request.organization_user
            facturation_refund.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )
        return context


class OrgFacturationRefundUpdateView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    mixins.OrgFormMixin,
    # mixins.UserFormMixin,
    UpdateView,
):
    model = models.FacturationRefund
    form_class = forms.FacturationRefundForm
    template_name = "orders/facturation_refund_edit.html"
    permission_required = ("orders.change_facturationrefund",)
    facturation = None

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_refund_change.html#change"]
        return ["orders/facturation_refund_change.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:facturation_refund_list",
            kwargs={
                "organization": self.request.organization.slug,
                "facturation": self.kwargs.get("facturation"),
            },
        )

    def get_form_kwargs(self):
        kwargs = super(OrgFacturationRefundUpdateView, self).get_form_kwargs()
        kwargs.update(
            {
                "organization": self.request.organization,
                # "organization_user": self.request.organization_user,
                "facturation": self.kwargs.get("facturation"),
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facturation"] = get_object_or_404(
            models.Facturation, pk=self.kwargs.get("facturation")
        )
        return context


class OrgFacturationRefundDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.FacturationRefund
    template_name = "orders/facturation_refund_confirm_delete.html"
    permission_required = ("orders.delete_facturationrefund",)

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
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:facturation_refund_list",
            kwargs={
                "organization": self.request.organization.slug,
                "facturation": self.kwargs.get("facturation"),
            },
        )


class OrgFacturationRefundDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.FacturationRefund
    context_object_name = "FacturationRefund"
    template_name = "orders/facturation_refund_detail.html"
    permission_required = ("orders.view_facturationrefund",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/facturation_refund_detail.html#detail"]
        return ["orders/facturation_refund_detail.html"]

    def get_object(self, queryset=None):
        self.object = get_object_or_404(
            models.FacturationRefund, pk=self.kwargs.get("pk")
        )
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OrgTransactionListView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    FilterView,
):
    model = models.Transaction
    template_name = "orders/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 30
    permission_required = ("transactions.view_transaction",)
    filterset_class = orders_filters.TransactionFilter

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["orders/transaction_list.html#list"]
            return ["orders/transaction_list.html#list"]
        return ["orders/transaction_list.html"]

    def get_queryset(self):
        return (
            models.Transaction.objects.filter(organization=self.request.organization)
            .select_related("organization_user")
            .order_by("-created")
        )

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        if self.request.htmx:
            return replace_url(
                response, self.request.get_full_path()
            )  # Push updated URL
        return response


class OrgTransactionAddView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    CreateView,
):
    model = models.Transaction
    form_class = forms.TransactionForm
    template_name = "orders/transaction_add.html"
    permission_required = ("transactions.add_transaction",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/transaction_add.html#add"]
        return ["orders/transaction_add.html"]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization_user"] = self.request.organization_user
        return kwargs

    def form_valid(self, form):
        transaction = form.save()
        messages.success(self.request, f"Transaction {transaction} saved successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, f"Transaction failed to be saved. Please check the form."
        )
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:transaction_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgTransactionChangeView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    mixins.OrgFormMixin,
    UpdateView,
):
    model = models.Transaction
    form_class = forms.TransactionForm
    template_name = "orders/transaction_change.html"
    permission_required = ("transactions.change_transaction",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/transaction_change.html#change"]
        return ["orders/transaction_change.html"]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization_user"] = self.request.organization_user
        return kwargs

    def form_valid(self, form):
        transaction = form.save()
        messages.success(
            self.request, f"Transaction {transaction} updated successfully"
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, f"Error updating transaction {self.get_object()}")
        return super().form_invalid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:orders:transaction_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgTransactionDeleteView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DeleteView,
):
    model = models.Transaction
    template_name = "orders/transaction_confirm_delete.html"
    permission_required = ("transactions.delete_transaction",)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get("HX-Request"):
            try:
                self.object.delete()
                messages.success(self.request, f"{self.object} deleted successfully")
                return HttpResponseRedirect(self.get_success_url())
            except ProtectedError as e:
                related_objects = e.protected_objects
                related_model_names = {
                    rel._meta.verbose_name for rel in related_objects
                }

                if related_model_names:
                    messages.error(
                        request,
                        f"This {self.object._meta.verbose_name} cannot be deleted because it is linked to: {', '.join(related_model_names)}.",
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
            "organization_features:orders:transaction_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgTransactionDetailView(
    LoginRequiredMixin,
    mixins.OrgPermissionRequiredMixin,
    mixins.MembershipRequiredMixin,
    DetailView,
):
    model = models.Transaction
    context_object_name = "transaction"
    template_name = "orders/transaction_detail.html"
    permission_required = ("transactions.view_transaction",)

    def get_template_names(self):
        if self.request.htmx:
            return ["orders/transaction_detail.html#detail"]
        return ["orders/transaction_detail.html"]
