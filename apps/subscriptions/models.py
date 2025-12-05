from datetime import datetime

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.organization.models import Organization


class Feature(BaseModel):
    name = models.CharField(max_length=100)
    code = models.PositiveIntegerField(_("code"), unique=True)

    def __str__(self) -> str:
        return self.name

    def generate_next_code(self):
        # Get the highest existing code and increment it
        highest_code = self.__class__.objects.filter(
            organization=self.organization,
            enrolled_student=self.enrolled_student,
        ).aggregate(models.Max("code"))["code__max"]
        if highest_code:
            # Increment the highest code
            next_code = int(highest_code) + 1
        else:
            # Start with some initial value if no records exist
            next_code = 1

        # Format the code as needed (e.g., with leading zeros)
        # formatted_code = f"{next_code:03}"  # Adjust the format as needed
        formatted_code = f"{next_code}"  # Adjust the format as needed

        return formatted_code

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_next_code()
        return super().save(*args, **kwargs)


class Plan(BaseModel):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    monthly_price = models.FloatField(default=0)
    yearly_price = models.FloatField(default=0)
    is_popular = models.BooleanField(default=False)
    is_enterprise = models.BooleanField(default=False)

    features = models.ManyToManyField(Feature, through="PlanFeature")

    def __str__(self):
        return self.name


class PlanFeature(BaseModel):
    feature = models.ForeignKey(
        Feature, on_delete=models.PROTECT, related_name="plan_features"
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name="plan_features"
    )
    is_powerful = models.BooleanField(default=False)

    class Meta:
        unique_together = ("feature", "plan")

    def __str__(self) -> str:
        return f"{str(self.plan)} | {self.feature}"


class Subscription(BaseModel):
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name="subscriptions"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="subscriptions"
    )
    start_time = models.DateTimeField()
    ends_time = models.DateTimeField()
    paid_status = models.BooleanField(default=False)  # payment gateway

    @property
    def is_active(self):
        return self.start_time <= timezone.now() <= self.ends_time

    def __str__(self):
        return (
            f"{self.organization.name} has subscribed to {self.plan.name} plan"
        )
