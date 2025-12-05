from django.contrib.auth.models import Group
from rest_framework import serializers

from apps.orders import models as order_models
from apps.organization import models as org_models
from apps.users.models import User


class ReportItemSerializer(serializers.Serializer):
    application = serializers.CharField()
    organization = serializers.CharField()
    type = serializers.CharField()
    name = serializers.CharField()
    total = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
