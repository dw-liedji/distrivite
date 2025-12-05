import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import BaseModel


class PaymentMethod(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    fees = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self) -> str:
        return self.name


class Payment(BaseModel):

    # product polymorphism implementation for association with different product models
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    generic_product_object = GenericForeignKey("content_type", "object_id")

    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = models.PositiveIntegerField(help_text="In CFA")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    transactionID = models.CharField(max_length=100, blank=True, null=True)
    conversationID = models.CharField(max_length=100, blank=True, null=True)
    reference = models.CharField(
        max_length=100,
        default=uuid.uuid4,
        blank=True,
        help_text="The reference ID associated with this payment.",
    )
    phone = models.CharField(
        max_length=12,
        verbose_name="Enter your payment number",
        help_text="example. 23767xxxxxxxx",
    )

    @property
    def payment_id(self):
        return str(self.id)

    @property
    def amount_display(self):
        return "${:,.2f}".format(self.amount / 100.0)

    def __str__(self):
        return self.user.business.name
