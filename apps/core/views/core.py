import weasyprint
from dal import autocomplete
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, redirect, render
from django.template.loader import render_to_string
from taggit.models import Tag
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from apps.core import services
from apps.organization.models import Organization


@login_required
def help(request):
    return render(request, "core/pages/help.html", {})


def terms(request):
    return render(request, "core/pages/terms.html", {})


def privacy(request):
    return render(request, "core/pages/privacy.html", {})


def subprocessors(request):
    return render(request, "core/pages/subprocessors.html", {})


def security(request):
    return render(request, "core/pages/security.html", {})


# Error pages
def handle_400(request, *args, **kwargs):
    return render(request, "core/pages/error/400.html", {})


def handle_403(request, *args, **kwargs):
    return render(request, "core/pages/error/403.html", {})


def handle_404(request, *args, **kwargs):
    return render(request, "core/pages/error/404.html", {})


def handle_500(request, *args, **kwargs):
    return render(request, "core/pages/error/500.html", {})


from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView


class HomePage(TemplateView):
    template_name = "core/index.html"

    def get(self, request, *args, **kwargs):
        # Perform the redirect here if the user is authenticated and is a Customer
        return HttpResponseRedirect(reverse("users:accounts"))
        # return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any other context you need here
        return context


def receipt(request):
    # return render(request, "core/receiptopticiop.html")
    return services.render_pdf(
        request,
        context={},
        html_path="core/receiptopticiop.html",
        output_filename="receipt",
    )
