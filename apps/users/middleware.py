class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, "profile"):
            # timezone.activate(
            #     request.user.profile.timezone
            # )  # Assuming user.profile.timezone is the user's preferred time zone
            pass

        response = self.get_response(request)
        return response
