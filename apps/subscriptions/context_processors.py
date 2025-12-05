from .models import Subscription


def subscription(request):
    """
    Return context variables required by apps that use Django's authentication
    system.

    If there is no 'user' attribute in the request, use AnonymousUser (from
    django.contrib.auth).
    """
    if hasattr(request, "organization_user"):
        organization_subscription = (
            Subscription.objects.filter(organization=request.organization)
            .prefetch_related("plan__plan_features")
            .last()
        )
        organization_features = []
        if organization_subscription:
            organization_features = [
                plan_feature.feature.name
                for plan_feature in organization_subscription.plan.plan_features.all()
            ]

        return {
            "organization_subscription": organization_subscription,
            "organization_features": organization_features,
        }
    else:
        from django.contrib.auth.models import AnonymousUser

        organization_user = AnonymousUser()
    return {
        "organization_user": organization_user,
    }
