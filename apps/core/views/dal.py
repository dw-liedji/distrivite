from dal import autocomplete

from apps.organization.models import Organization
from apps.users.models import User
from apps.orders.models import Customer, Category, Batch, Item
from django.db.models import Q

from datetime import datetime


class OrgUserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return User.objects.none()

        qs = User.objects.all()

        if self.q:
            qs = qs.filter(username__istartswith=self.q)

        return qs


class OrgCategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # If not authenticated or not in an organization
        if not self.request.user:
            return Category.objects.none()

        # Get the organization
        organization_id = self.forwarded.get("organization")
        print("organization_id:", organization_id)

        organization = Organization.objects.get(id=organization_id)
        print(f"{self.request.user} is a user of {organization}")
        if not organization:
            return Category.objects.none()

        if organization.id not in list(
            self.request.user.organization_organization.values_list("id", flat=True)
        ):
            return Category.objects.none()

        # Filter by organization (trough model)
        qs = Category.objects.filter(organization=organization)

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class OrgCustomerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # If not authenticated or not in an organization
        if not self.request.user:
            return Customer.objects.none()

        # Get the organization
        organization_id = self.forwarded.get("organization")

        organization = Organization.objects.get(id=organization_id)
        if not organization:
            return Customer.objects.none()

        if organization.id not in list(
            self.request.user.organization_organization.values_list("id", flat=True)
        ):
            return Customer.objects.none()

        # Filter by organization (trough model)
        qs = Customer.objects.filter(organization=organization)

        if self.q:
            qs = qs.filter(username__icontains=self.q)

        return qs


from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden
from apps.orders.models import Customer


from django.views.generic import ListView


class AutocompleteBaseView(ListView):
    template_name = "widgets/autocomplete_results.html"
    context_object_name = "objects"
    model = Customer  # Override in subclass
    search_field = "username"  # Field to search against
    filter_fields = []  # Fields to filter by

    def get_queryset(self):
        queryset = super().get_queryset()

        query = self.request.GET.get("q", "")
        organization = self.request.GET.get("organization", "")

        if organization:
            queryset = queryset.filter(organization_id=organization)

        if query:
            queryset = queryset.filter(**{f"{self.search_field}__icontains": query})

        for field in self.filter_fields:
            value = self.request.GET.get(field)
            if value:
                queryset = queryset.filter(**{field: value})

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["input_id"] = self.request.GET.get("input_id")
        return context


class OrgBatchAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # If not authenticated or not in an organization
        if not self.request.user:
            return Batch.objects.none()

        # Get the organization
        organization_id = self.forwarded.get("organization")
        print("organization_id:", organization_id)

        organization = Organization.objects.get(id=organization_id)
        print(f"{self.request.user} is a user of {organization}")
        if not organization:
            return Batch.objects.none()

        if organization.id not in list(
            self.request.user.organization_organization.values_list("id", flat=True)
        ):
            return Batch.objects.none()

        # Filter by organization (trough model)
        qs = (
            Batch.objects.filter(
                organization=organization,
                expiration_date__gte=datetime.now().date(),
            )
            .filter(Q(Q(quantity__gt=0)))
            .select_related("item__category")
            .order_by("expiration_date")
        )

        if self.q:
            qs = qs.filter(Q(Q(item__name__icontains=self.q)))

        return qs


class OrgItemAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # If not authenticated or not in an organization
        if not self.request.user:
            return Item.objects.none()

        # Get the organization
        organization_id = self.forwarded.get("organization")
        print("organization_id:", organization_id)

        organization = Organization.objects.get(id=organization_id)
        if not organization:
            return Item.objects.none()

        if organization.id not in list(
            self.request.user.organization_organization.values_list("id", flat=True)
        ):
            return Item.objects.none()

        # Filter by organization (trough model)
        qs = Item.objects.filter(organization=organization).select_related("category")

        if self.q:
            qs = qs.filter(Q(Q(name__icontains=self.q)))

        return qs
