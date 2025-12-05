from django.conf import settings
from django_hosts import host, patterns

host_patterns = patterns(
    "",
    host(r"help", settings.ROOT_URLCONF, name="help"),
    host(r"www", settings.ROOT_URLCONF, name="www"),
    host(
        r"(?P<organization_slug>\w+).*",
        "apps.organization.features_urls",
        name="organization-area",
    ),
)
