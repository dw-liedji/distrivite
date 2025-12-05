from django.db import models


class OrganizationRelatedModel(models.Model):
    """Abstract class used by models that belong to a Organization"""

    organization = models.ForeignKey(
        "quanta_organizations.Organization",
        related_name="%(class)s",
        on_delete=models.CASCADE,
        editable=False,
    )

    class Meta:
        abstract = True
