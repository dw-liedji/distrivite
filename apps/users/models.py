import sys
from io import BytesIO
from typing import List

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from PIL import Image

# from apps.notifications.models import Notification
from timezone_field import TimeZoneField

from apps.core.models import BaseModel

# from apps.notifications.models import Notification
# from apps.payments.PaymentMixins import PaymentMixins
from apps.users.fields import QuantaNumberField


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field. But a email as primary identifier"""

    use_in_migrations = True

    def _create_user(
        self,
        email,
        username,
        password,
        **extra_fields,
    ):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        email,
        username,
        password=None,
        **extra_fields,
    ):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        user = self._create_user(
            email=email,
            username=username,
            password=password,
            **extra_fields,
        )

        return user

    def create_superuser(self, username, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self._create_user(
            email=email,
            username=username,
            password=password,
            **extra_fields,
        )
        # user.username = username
        # user.save()
        # print("Your login credential is:", user.username)

        return user


# class User(AbstractUser, PaymentMixins, BaseModel):
class User(BaseModel, AbstractUser):
    first_name = None
    last_name = None
    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(max_length=100, verbose_name="login")
    is_patient = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    image = models.ImageField(upload_to="accounts/images/", blank=True, null=True)
    phone_number = PhoneNumberField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Opening the uploaded image
        if self.image:
            im = Image.open(self.image)

            output = BytesIO()

            # Resize/modify the image
            im = im.resize((150, 150)).convert("RGB")

            # after modifications, save it to the output
            im.save(output, format="JPEG", optimize=True, quality=25)
            output.seek(0)

            # change the imagefield value to be the newley modifed image value
            self.image = InMemoryUploadedFile(
                output,
                "ImageField",
                "%s.jpg" % self.image.name.split(".")[0],
                "image/jpeg",
                sys.getsizeof(output),
                None,
            )
            super(User, self).save(*args, **kwargs)
        else:
            super(User, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.username} | {self.email}"

    objects = UserManager()

    class Meta:
        ordering = ["username"]
