import os

from decouple import config  # For environment variables

# Load environment variables from .env
from .common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-58hcg7x8%w8cx^k$-_i@nd2l*u-4%ofxn(nq)(#u#rchg56^a!"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ("debug_toolbar",)
# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases


# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "distrivitedb3",
        "USER": "liedji",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/


INSTALLED_APPS += (
    # "cloudinary_storage",
    # "cloudinary",
    "django_cleanup.apps.CleanupConfig",
)


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
MEDIA_URL = f"https://{STORAGES['default']['OPTIONS']['custom_domain']}/media/"

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

# MEDIA_URL = "/media/"
# MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

# DATABASES = {"default": dj_database_url.config()}

# IOT SETTINGS WITH MQTT CLIENT
MQTT_SERVER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_USER = ""
MQTT_PASSWORD = ""


INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]
