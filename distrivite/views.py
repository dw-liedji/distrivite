from django.shortcuts import redirect


def language_redirect(request):
    return redirect("core:index")
