from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from . import forms
from .models import User

# from apps.notifications.models import Notification, NotificationFactory


def user_settings(request):
    return render(request, "users/settings.html", {"section": "settings"})


from django.contrib.auth import authenticate, login
from django.views.generic import CreateView, TemplateView


class RegisterDone(TemplateView):
    template_name = "users/register_done.html"


class UserCreateView(CreateView):
    model = User
    form_class = forms.UserRegistrationForm
    template_name = "users/register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def user_saved(self, form, user):
        user = authenticate(email=user.email, password=form.cleaned_data["password"])
        login(self.request, user)
        return user

    def form_valid(self, form):
        # Create a new user object but avoid saving it yet
        new_user = form.save(commit=False)
        # Set the chosen password
        # new_user.set_password(form.cleaned_data["password"])
        # Save the User object
        new_user.save()
        # Create the user profile
        self.user_saved(form=form, user=new_user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("users:register_done")


class AccountPage(LoginRequiredMixin, TemplateView):
    template_name = "users/accounts.html"

    def get(self, request, *args, **kwargs):
        # Perform the redirect here if the user is authenticated and is a Customer
        # if self.request.user.is_authenticated and self.request.user.is_patient:
        #     return HttpResponseRedirect(reverse("orders:user_order_list"))
        return super().get(request, *args, **kwargs)


@login_required
def user_organizations(request):
    return render(
        request,
        "users/organizations.html",
        {
            "organizations": Organization.objects.active_for_user(
                user=request.user
            ).select_related("owner__organization_user__user")
        },
    )


@login_required
def user_study_organizations(request):
    return render(
        request,
        "users/organizations.html",
        {
            "organizations": Organization.objects.filter(
                students__user=request.user
            ).select_related("owner__organization_user__user")
        },
    )


from apps.organization.models import (
    Organization,
    OrganizationInvitation,
    OrganizationUser,
)


@login_required
def user_invitations(request):
    return render(
        request,
        "users/invitations.html",
        {
            "invitations": OrganizationInvitation.objects.filter(
                invitee_identifier=request.user.email,
                status=OrganizationInvitation.InvitationStatus.PENDING,
            )
        },
    )


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View

from . import forms


@method_decorator(login_required, name="dispatch")
class UserEditView(View):
    template_name = "users/edit.html"
    success_url = reverse_lazy(
        "users:settings"
    )  # Change 'profile-edit' to your actual URL name

    def get(self, request, *args, **kwargs):
        user_form = forms.UserEditForm(instance=request.user)
        # profile_form = forms.ProfileEditForm(instance=request.user.profile)
        return render(
            request,
            self.template_name,
            {"user_form": user_form},
        )

    def post(self, request, *args, **kwargs):
        user_form = forms.UserEditForm(
            instance=request.user,
            data=request.POST,
            files=request.FILES,
        )

        if user_form.is_valid():
            user_form.save()
            messages.success(request, "Profile updated successfully")
            return redirect(self.success_url)
        else:
            messages.error(request, "Error updating your profile")
            return render(
                request,
                self.template_name,
                {"user_form": user_form},
            )


@login_required
def user_invitation_accept(request, pk):
    invitation = get_object_or_404(OrganizationInvitation, pk=pk)
    invitation.status = OrganizationInvitation.InvitationStatus.ACCEPTED
    invitation.save()
    # invitation.organization.organization_users.add(request.user)
    organization_user = OrganizationUser(
        organization=invitation.organization, user=request.user, is_active=True
    )
    organization_user.save()
    return render(
        request,
        "users/invitations.html",
        {
            "invitations": OrganizationInvitation.objects.filter(
                invitee_identifier=request.user.email,
                status=OrganizationInvitation.InvitationStatus.PENDING,
            )
        },
    )


@login_required
def user_invitation_rejected(request, pk):
    invitation = get_object_or_404(OrganizationInvitation, pk=pk)
    invitation.status = OrganizationInvitation.InvitationStatus.REJECTED
    invitation.save()
    # invitation.organization.organization_users.add(request.user)

    return render(
        request,
        "users/invitations.html",
        {
            "invitations": OrganizationInvitation.objects.filter(
                invitee_identifier=request.user.email,
                status=OrganizationInvitation.InvitationStatus.PENDING,
            )
        },
    )


@login_required
def user_notifications(request):
    # if request.user.notifications.count() == 0:
    #     NotificationFactory().for_user(request.user).send_notification(
    #         sender=request.user,  # using the user themselves as actor.
    #         title="This is your first notification!",
    #     )

    notifications = request.user.notifications_all

    return render(
        request,
        "users/notifications.html",
        {"notifications": notifications},
    )
