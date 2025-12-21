from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from apps.core import decorators as core_decorators

# from apps.boxes.models import Box
from apps.organization import forms, models
from apps.organization.forms import (
    OrganizationForm,
    OrganizationUpdateForm,
    OrganizationUserAddForm,
    OrganizationUserChangeForm,
)
from apps.organization.mixins import (
    AdminRequiredMixin,
    MembershipRequiredMixin,
    OrgFormMixin,
)
from apps.organization.models import (
    Organization,
    OrganizationGroup,
)
from apps.users import forms as user_forms  # Import your forms option_module


@login_required
def organization_create(request):
    organization_create_form = OrganizationForm(request.POST or None)
    if request.method == "POST":
        if organization_create_form.is_valid():
            organization = organization_create_form.save()
            organization_user = organization.add_user(request.user, is_admin=True)
            organization_user.is_active = True
            organization_user.save()

            # Box.objects.create(
            #     organization_id=organization.pk,
            # )
            messages.add_message(
                request,
                messages.SUCCESS,
                "{} created".format(organization.name),
            )

            return redirect("users:organizations")
        else:
            errors = ",".join(
                map(
                    lambda err: str(err[0]),
                    organization_create_form.errors.values(),
                )
            )
            messages.add_message(
                request,
                messages.ERROR,
                organization_create_form.non_field_errors().as_text() + errors,
            )
            print(organization_create_form.non_field_errors().as_text() + errors)
    return render(
        request,
        "organization/create.html",
        {"organization_create_form": organization_create_form},
    )


def organization_dashboard(request):
    context = {"organization": request.organization}
    return render(request, "organization/dashboard.html", context)


class OrganizationUpdateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    AdminRequiredMixin,
    UpdateView,
):
    model = Organization
    form_class = OrganizationUpdateForm
    template_name = "organization/settings/org_change.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/settings/org_change.html#change"]
        return ["organization/settings/org_change.html"]

    def get_object(self, queryset=None):
        organization = get_object_or_404(Organization, pk=self.request.organization.pk)
        return organization

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:org_things:org_change",
            kwargs={"organization": self.request.organization.slug},
        )


@login_required
def organization_settings(request):
    organization_form = OrganizationUpdateForm(
        request.POST or None,
        request.FILES,
        instance=request.organization,
    )
    if request.method == "POST" and organization_form.is_valid():
        organization_form.save()
        print(organization_form.cleaned_data)
        messages.add_message(
            request, messages.SUCCESS, "Organization updated successfully"
        )

    return render(
        request,
        "organization/settings/settings.html",
        {
            "organization_form": organization_form,
        },
    )


class OrgUserListView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    AdminRequiredMixin,
    ListView,
):
    model = models.OrganizationUser
    template_name = "organization/settings/org_user_list.html"
    context_object_name = "organization_users"
    paginate_by = 20

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["organization/settings/org_user_list.html#list"]
            return ["organization/settings/org_user_list.html#list"]
        return ["organization/settings/org_user_list.html"]

    def get_queryset(self):
        return (
            models.OrganizationUser.objects.for_organization(
                organization=self.request.organization
            )
            .order_by("-created")
            .all()
        )


class OrgUserAddView(View):
    template_name = (
        "organization/new_org_user.html"  # Change to your actual template name
    )

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/new_org_user.html#add"]
        return ["organization/new_org_user.html"]

    def get(self, request, *args, **kwargs):
        user_form = user_forms.InternalUserRegisterForm()
        org_user_form = OrganizationUserAddForm(organization=request.organization.id)
        return render(
            request,
            self.get_template_names(),
            {
                "user_form": user_form,
                "org_user_form": org_user_form,
            },
        )

    def post(self, request, *args, **kwargs):
        user_form = user_forms.InternalUserRegisterForm(data=request.POST)

        org_user_form = OrganizationUserAddForm(
            organization=request.organization, data=request.POST
        )

        if user_form.is_valid() and org_user_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                user.password = make_password("DataViteAI")
                user.save()

                org_user = org_user_form.save(commit=False)
                org_user.user = user
                org_user.save()

                # Log in the user
                # login(request, user)

            messages.success(request, "Instructor created successfully")
            return redirect(self.get_success_url())
        else:
            messages.error(request, "Error creating your instructor")
            return render(
                request,
                self.get_template_names(),
                {
                    "user_form": user_form,
                    "org_user_form": org_user_form,
                },
            )

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:org_things:org_user_list",
            kwargs={
                "organization": self.request.organization.slug,
            },
        )


class OrgUserChangeView(View):
    template_name = (
        "organization/new_org_user.html"  # Change to your actual template name
    )

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/org_user_change.html#change"]
        return ["organization/org_user_change.html"]

    def get(self, request, *args, **kwargs):
        organization_user = get_object_or_404(
            models.OrganizationUser, pk=self.kwargs.get("pk")
        )
        org_user_form = OrganizationUserChangeForm(
            organization=request.organization, instance=organization_user
        )
        user_form = user_forms.InternalUserRegisterForm(instance=organization_user.user)

        return render(
            request,
            self.get_template_names(),
            {
                "user_form": user_form,
                "org_user_form": org_user_form,
                "object": organization_user,
            },
        )

    def post(self, request, *args, **kwargs):
        org_user = get_object_or_404(models.OrganizationUser, pk=self.kwargs.get("pk"))

        org_user_form = OrganizationUserChangeForm(
            organization=request.organization, data=request.POST, instance=org_user
        )
        user_form = user_forms.InternalUserRegisterForm(
            data=request.POST, instance=org_user.user
        )

        if user_form.is_valid():
            with transaction.atomic():
                user_form.save()

                # You might need to adjust the code below based on your actual models
                org_user_form.save()

            messages.success(request, "Instructor updated successfully")
            return redirect(self.get_success_url())
        else:
            messages.error(request, "Error updating your Instructor")
            return render(
                request,
                self.get_template_names(),
                {
                    "user_form": user_form,
                    "org_user_form": org_user_form,
                },
            )

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:org_things:org_user_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgGroupListView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    AdminRequiredMixin,
    ListView,
):
    model = models.OrganizationGroup
    template_name = "organization/settings/org_group_list.html"
    context_object_name = "organization_groups"
    paginate_by = 20

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["organization/settings/org_group_list.html#list"]
            return ["organization/settings/org_group_list.html#list"]
        return ["organization/settings/org_group_list.html"]

    def get_queryset(self):
        return (
            models.OrganizationGroup.objects.for_organization(
                organization=self.request.organization
            )
            .order_by("-created")
            .all()
        )


class OrgGroupChangeView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    AdminRequiredMixin,
    OrgFormMixin,
    UpdateView,
):
    model = models.OrganizationGroup
    form_class = forms.OrganizationGroupForm
    template_name = "organization/settings/org_group_change.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/settings/org_group_change.html#change"]
        return ["organization/settings/org_group_change.html"]

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context["group"] = self.object
        return context

    def form_valid(self, form):
        """If the form is valid, save the associated model."""

        self.object = form.save()
        return super().form_valid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:org_things:org_group_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgGroupCreateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    CreateView,
):
    model = models.OrganizationGroup
    form_class = forms.OrganizationGroupForm
    template_name = "organization/settings/org_group_add.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/settings/org_group_add.html#add"]
        return ["organization/settings/org_group_add.html"]

    def form_valid(self, form):
        """If the form is valid, save the associated model."""

        self.object = form.save()
        return super().form_valid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:org_things:org_group_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgGroupDetailView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.OrganizationGroup
    context_object_name = "group"
    template_name = "organization/settings/group_detail.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/settings/org_group_detail.html#detail"]
        return ["organization/settings/org_group_detail.html"]


class OrgGroupDeleteView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.OrganizationGroup
    template_name = "organization/settings/group_delete.html"

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
            "organization_features:org_things:org_group_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgGroupUserListView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    AdminRequiredMixin,
    ListView,
):
    model = models.OrganizationUserGroup
    template_name = "organization/settings/org_group_user_list.html"
    context_object_name = "organization_group_users"
    paginate_by = 20
    group = None

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["organization/settings/org_group_user_list.html#list"]
            return ["organization/settings/org_group_user_list.html#list"]
        return ["organization/settings/org_group_user_list.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.group
        return context

    def get_queryset(self):
        self.group = get_object_or_404(OrganizationGroup, pk=self.kwargs.get("group"))

        return self.group.organization_user_groups.all().order_by("-created").all()


class OrgGroupUserCreateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    AdminRequiredMixin,
    OrgFormMixin,
    CreateView,
):
    form_class = forms.OrganizationUserGroupForm
    model = models.OrganizationUserGroup
    template_name = "organization/settings/org_group_user_add.html"
    group = None

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/settings/org_group_user_add.html#add"]
        return ["organization/settings/org_group_user_add.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:org_things:org_group_user_list",
            kwargs={
                "organization": self.request.organization.slug,
                "group": self.kwargs.get("group"),
            },
        )

    def get_form_kwargs(self):
        kwargs = super(OrgGroupUserCreateView, self).get_form_kwargs()
        self.group = get_object_or_404(
            models.OrganizationGroup, pk=self.kwargs.get("group")
        )
        kwargs.update(
            {
                "organization": self.request.organization,
                "organization_user": self.request.organization_user,
                "group": self.group,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.group
        return context


class OrgGroupUserUpdateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    AdminRequiredMixin,
    OrgFormMixin,
    UpdateView,
):
    form_class = forms.OrganizationUserGroupForm
    model = models.OrganizationUserGroup
    template_name = "organization/settings/group_user_change.html"
    group = None

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/settings/org_group_user_change.html#change"]
        return ["organization/settings/org_group_user_change.html"]

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:org_things:org_group_user_list",
            kwargs={
                "organization": self.request.organization.slug,
                "group": self.kwargs.get("group"),
            },
        )

    def get_form_kwargs(self):
        kwargs = super(OrgGroupUserUpdateView, self).get_form_kwargs()
        self.group = get_object_or_404(
            models.OrganizationGroup, pk=self.kwargs.get("group")
        )
        kwargs.update(
            {
                "organization": self.request.organization,
                "organization_user": self.request.organization_user,
                "group": self.group,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.group
        return context


class OrgGroupUserDetailView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.OrganizationUserGroup
    context_object_name = "organization_user_group"
    template_name = "organization/settings/org_group_user_detail.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/settings/org_group_user_detail.html#detail"]
        return ["organization/settings/org_group_user_detail.html"]

    def get_object(self, queryset=None):
        self.object = get_object_or_404(
            models.OrganizationUserGroup, pk=self.kwargs.get("pk")
        )
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = get_object_or_404(
            models.OrganizationGroup, pk=self.kwargs.get("group")
        )
        return context


class OrgGroupUserDeleteView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.OrganizationUserGroup
    template_name = "organization/settings/group_user_delete.html"

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
            "organization_features:org_things:org_group_user_list",
            kwargs={
                "organization": self.request.organization.slug,
                "group": self.kwargs.get("group"),
            },
        )


class OrgInvitationListView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    AdminRequiredMixin,
    ListView,
):
    model = models.OrganizationInvitation
    template_name = "organization/settings/org_invitation_list.html"
    context_object_name = "org_invitations"
    paginate_by = 20

    def get_template_names(self):
        if self.request.htmx:
            if self.request.headers.get("HX-Request-Source") == "sidebar":
                return ["organization/settings/org_invitation_list.html#list"]
            return ["organization/settings/org_invitation_list.html#list"]
        return ["organization/settings/org_invitation_list.html"]

    def get_queryset(self):
        return (
            models.OrganizationInvitation.objects.for_organization(
                organization=self.request.organization
            )
            .order_by("-created")
            .all()
        )


class OrgInvitationCreateView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    CreateView,
):
    model = models.OrganizationInvitation
    form_class = forms.OrganizationInvitationForm
    template_name = "organization/settings/invitation_add.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/settings/org_invitation_add.html#add"]
        return ["organization/settings/org_invitation_add.html"]

    def form_valid(self, form):
        """If the form is valid, save the associated model."""

        self.object = form.save()
        return super().form_valid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:org_things:org_invitation_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgInvitationChangeView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    OrgFormMixin,
    UpdateView,
):
    model = models.OrganizationInvitation
    form_class = forms.OrganizationInvitationForm
    template_name = "organization/settings/org_invitation_change.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/settings/org_invitation_change.html#change"]
        return ["organization/settings/org_invitation_change.html"]

    def form_valid(self, form):
        """If the form is valid, save the associated model."""

        self.object = form.save()
        return super().form_valid(form)

    @core_decorators.preserve_query_params()
    def get_success_url(self):
        return reverse_lazy(
            "organization_features:org_things:org_invitation_list",
            kwargs={"organization": self.request.organization.slug},
        )


class OrgInvitationDetailView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DetailView,
):
    model = models.OrganizationInvitation
    context_object_name = "invitation"
    template_name = "organization/settings/invitation_detail.html"

    def get_template_names(self):
        if self.request.htmx:
            return ["organization/settings/org_invitation_detail.html#detail"]
        return ["organization/settings/org_invitation_detail.html"]


class OrgInvitationDeleteView(
    LoginRequiredMixin,
    MembershipRequiredMixin,
    # AdminRequiredMixin,
    DeleteView,
):
    model = models.OrganizationInvitation
    template_name = "organization/settings/invitation_delete.html"

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
            "organization_features:org_things:org_invitation_list",
            kwargs={"organization": self.request.organization.slug},
        )
