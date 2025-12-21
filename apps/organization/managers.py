from django.db import models
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404

from apps.users.models import AbstractUser as User


class OrgUserMixin(object):
    def for_user(self, user):
        return self.get_queryset().filter(user=user)

    def for_active_user(self, user):
        return self.get_queryset().filter(user=user, is_active=True)


class OrgOwnerMixin(object):
    def for_user(self, user):
        # If we are receiving a string, it's most likely a slug,
        # so we do a lookup to get the organization by slug
        if type(user) is str:
            user = get_object_or_404(User, pk=user.pk)
        return self.get_queryset().filter(organization_user__user=user)


class OrgFeatureMixin(object):
    def for_organization(self, organization):
        from .models import Organization

        # If we are receiving a string or integer, it's most likely an ID or a slug,
        # so we do a lookup to get the organization by ID or slug

        if isinstance(organization, QuerySet):
            # organization = Organization.objects.filter(pk__in=organization)
            return self.get_queryset().filter(organization__in=organization)
        elif isinstance(organization, (str, int)):
            organization = get_object_or_404(Organization, slug=organization)
        return self.get_queryset().filter(organization=organization)


class OrgFeatureQuerySet(QuerySet, OrgFeatureMixin):
    pass


class OrgUserQuerySet(QuerySet, OrgFeatureMixin, OrgUserMixin):
    pass


class OrgOwnerQuerySet(QuerySet, OrgFeatureMixin, OrgOwnerMixin):
    pass


class OrgManager(models.Manager):
    def for_user(self, user):
        # If we are receiving a string, it's most likely a slug,
        # so we do a lookup to get the organization by slug
        if type(user) is str:
            user = get_object_or_404(User, pk=user.pk)
        return super(OrgManager, self).get_queryset().filter(users=user)

    def active_for_user(self, user):
        # If we are receiving a string, it's most likely a slug,
        # so we do a lookup to get the organization by slug
        if type(user) is str:
            user = get_object_or_404(User, pk=user.pk)
        return (
            super(OrgManager, self)
            .get_queryset()
            .filter(
                organization_users__user=user,
                organization_users__is_active=True,
            )
        )

    def active_for_student_user(self, user):
        # If we are receiving a string, it's most likely a slug,
        # so we do a lookup to get the organization by slug
        if type(user) is str:
            user = get_object_or_404(User, pk=user.pk)
        return (
            super(OrgManager, self)
            .get_queryset()
            .filter(
                students__user=user,
                # organization_users__is_active=True,
            )
        )


class OrgFeatureManager(models.Manager, OrgFeatureMixin):
    def get_query_set(self):
        return OrgFeatureQuerySet(self.model, using=self._db)


class OrgUserManager(models.Manager, OrgFeatureMixin, OrgUserMixin):
    def get_query_set(self):
        return OrgUserQuerySet(self.model, using=self._db)


class OrgOwnerManager(models.Manager, OrgFeatureMixin, OrgOwnerMixin):
    def get_query_set(self):
        return OrgOwnerQuerySet(self.model, using=self._db)
