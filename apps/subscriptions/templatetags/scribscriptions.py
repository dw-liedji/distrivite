from urllib.parse import urlparse, urlunparse

from django import template
from django.http import QueryDict

from apps.organization.models import Organization

register = template.Library()


# @register.filter
# def plan_feature(plan, feature_item):
#     feature_item_value = FeatureItemPlanValue.objects.filter(
#         plan=plan, feature_item=feature_item
#     ).first()
#     return feature_item_value.value
