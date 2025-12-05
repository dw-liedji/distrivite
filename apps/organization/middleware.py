import zoneinfo

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.organization.models import Organization, OrganizationUser


class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if view_kwargs.get("organization"):
            organization_slug = view_kwargs.get("organization")
            view_kwargs.pop("organization", None)

            request.organization_slug = organization_slug
            # Get the organization object in the class that we use
            organization = get_object_or_404(Organization, slug=organization_slug)

            request.organization = organization

            # In the case of a POST request, we also change the payload and
            # add the organization, so it's available for the forms.
            if request.method == "POST":
                # Since the original is immutable, we make a copy
                request.POST = request.POST.copy()
                # request.POST["organization"] = organization

            # If we are logged in, try getting the organization user we currently are using
            if not request.user.is_anonymous:
                organization_user = OrganizationUser.objects.filter(
                    organization=organization, user=request.user
                ).first()
                if organization_user:
                    request.organization_user = organization_user


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = "Africa/Douala"
        if tzname:
            timezone.activate(zoneinfo.ZoneInfo(tzname))
        else:
            timezone.deactivate()
        return self.get_response(request)
