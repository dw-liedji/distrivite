from datetime import datetime

from django.db import models

# https://www.youtube.com/watch?v=Mw__Pw1iGgA&ab_channel=DjangoLessons


class PaymentMixins(models.Model):
    paid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def has_paid(self):
        if self.paid_until is None:
            return False
        return datetime.today() < self.paid_until
