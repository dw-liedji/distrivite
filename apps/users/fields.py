import datetime

from django.db import models


class QuantaNumberField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 20)
        super().__init__(*args, **kwargs)

    def _generate_quanta_number(self):
        # Generate a quanta number based on the current timestamp
        now = datetime.datetime.utcnow()
        timestamp_int = int(datetime.datetime.timestamp(now))
        return f"Q{timestamp_int}"

    def pre_save(self, model_instance, add):
        if add:
            quanta_number = self._generate_quanta_number()
            setattr(model_instance, self.attname, quanta_number)
        else:
            quanta_number = getattr(model_instance, self.attname)
        return quanta_number


from django.core.exceptions import ValidationError
from django.db import models
from pytz import all_timezones, timezone
