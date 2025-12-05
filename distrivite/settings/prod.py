import os

import dj_database_url

from .common import *
from decouple import config  # For environment variables

# |Liedji6Wenkack7Dagobert8|Python2&3@code.py|
# admin@opticio.com
# Python3.py
DEBUG = True

ALLOWED_HOSTS = [
    "distrivite-0121b123ce88.herokuapp.com",
]

ROOT_URLCONF = "distrivite.urls"
SECRET_KEY = os.environ["SECRET_KEY"]

INSTALLED_APPS += (
    # "cloudinary_storage",
    # "cloudinary",
    "django_cleanup.apps.CleanupConfig",
)

DATABASES = {"default": dj_database_url.config()}

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

# Django 4.2+ STORAGES configuration
STORAGES = {
    # Static files (CSS, JS, images)
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    # Media files (uploads)
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": config("AWS_ACCESS_KEY_ID"),
            "secret_key": config("AWS_SECRET_ACCESS_KEY"),
            "bucket_name": config("AWS_STORAGE_BUCKET_NAME"),
            "region_name": config("AWS_S3_REGION_NAME", "us-east-1"),
            "location": "media",  # Directory in S3 bucket for media files
            # "default_acl": "public-read",
            "file_overwrite": False,
            "custom_domain": f"{config('AWS_STORAGE_BUCKET_NAME')}.s3.amazonaws.com",
        },
    },
}

# Static/Media URL settings (adjust based on your S3 setup)
# STATIC_URL = f'https://{STORAGES["staticfiles"]["OPTIONS"]["custom_domain"]}/static/'
MEDIA_URL = f'https://{STORAGES["default"]["OPTIONS"]["custom_domain"]}/media/'


# STATIC_URL = "/static/"
# STATIC_ROOT = os.path.join(BASE_DIR, "static/")
# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# MEDIA_URL = "/media/"  # or any prefix you choose
# # DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
# DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.RawMediaCloudinaryStorage"


SECURE_PROXY_SSL_HEADER = ("X-Forwarded-Proto", "https")
SECURE_SSL_REDIRECT = True
