import uuid

from django.db import models
from model_utils.models import TimeStampedModel


class SimpleBaseModel(TimeStampedModel):
    class Meta:
        abstract = True


class BaseModel(SimpleBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    response = models.TextField(max_length=555)

    def __str__(self) -> str:
        return self.question
