import datetime
import random
import string

from django.db import models


class TranscriptNumberField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 20)
        kwargs.setdefault("unique", True)
        super().__init__(*args, **kwargs)

    def _generate_quanta_number(self):
        # Generate a quanta number based on the current timestamp and a random component
        now = datetime.datetime.utcnow()
        timestamp_int = int(datetime.datetime.timestamp(now))
        # Generate a random component (e.g., 6 random characters)
        # random_component = "".join(
        #     random.choice(string.ascii_letters + string.digits)
        #     for _ in range(4)
        # )
        # Generate a random component (e.g., 6 random characters)
        random_component = "".join(random.choice(string.digits) for _ in range(6))
        return f"{timestamp_int}Q{random_component}"

    def pre_save(self, model_instance, add):
        if add:
            quanta_number = self._generate_quanta_number()
            setattr(model_instance, self.attname, quanta_number)
        else:
            quanta_number = getattr(model_instance, self.attname)
        return quanta_number


class QuantaField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 20)
        kwargs.setdefault("unique", True)
        super().__init__(*args, **kwargs)

    def _generate_bill_number(self):
        # Generate a bill number based on the current timestamp
        now = datetime.datetime.utcnow()
        timestamp_string = now.strftime("%Y%m%d%H%M%S")
        timestamp_int = int(datetime.datetime.timestamp(now))
        # sequence_number = model_instance.__class__.objects.count() + 1
        sequence_number = random.randint(1000000, 9999999)
        bill_number = f"{timestamp_int}Q{sequence_number}"
        return bill_number

    def pre_save(self, model_instance, add):
        if add:
            quanta_number = self._generate_bill_number()
            setattr(model_instance, self.attname, quanta_number)
        else:
            quanta_number = getattr(model_instance, self.attname)
        return quanta_number


class ProfessionalBillNumberField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 20)
        super().__init__(*args, **kwargs)

    def _generate_bill_number(self):
        # Generate a bill number based on the current timestamp
        now = datetime.datetime.now(datetime.timezone.utc)
        timestamp_string = now.strftime("%Y%m%d%H%M%S")
        timestamp_int = int(datetime.datetime.timestamp(now))
        # sequence_number = model_instance.__class__.objects.count() + 1
        sequence_number = random.randint(1000, 9999)
        # bill_number = f"{timestamp_int}Q{sequence_number}"
        bill_number = f"{timestamp_int}"
        return bill_number

    def pre_save(self, model_instance, add):
        if add:
            bill_number = self._generate_bill_number()
            setattr(model_instance, self.attname, bill_number)
        else:
            bill_number = getattr(model_instance, self.attname)
        return bill_number


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
