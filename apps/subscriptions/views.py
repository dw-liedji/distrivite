from django.shortcuts import render


def pricing(request):
    return render(
        request,
        "subscriptions/pricing.html",
        context={},
    )
