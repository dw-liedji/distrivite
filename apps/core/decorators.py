from functools import wraps


def preserve_query_params(*exclude_params):
    """
    Decorator to preserve query parameters, excluding specified ones.
    """

    def decorator(view_method):
        @wraps(view_method)
        def wrapper(self, *args, **kwargs):
            # Get the current query parameters from the request
            query_params = self.request.GET.copy()

            # Remove excluded parameters
            for param in exclude_params:
                if param in query_params:
                    del query_params[param]

            # Call the original get_success_url method
            success_url = view_method(self, *args, **kwargs)

            # Append the remaining query parameters to the success URL
            if query_params:
                success_url = f"{success_url}?{query_params.urlencode()}"

            return success_url

        return wrapper

    return decorator
