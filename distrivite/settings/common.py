import codecs
import os
import sys
from datetime import timedelta
from pathlib import Path

from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition

INSTALLED_APPS = [
    # The following apps are required for django allauth:
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django.contrib.auth",
    "polymorphic",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Include the providers you want to enable:
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # external applications
    "django_extensions",
    "organizations",
    "djoser",
    # "django_hosts",
    "mptt",
    "crispy_forms",
    "crispy_bulma",
    "embed_video",
    # "taggit",
    "qr_code",
    "phonenumber_field",
    "import_export",
    "django_pivot",
    "rest_framework",
    "markdown",
    "django_htmx",
    "mathfilters",
    "django_filters",
    # "djmoney",
    "rosetta",
    "dal",  # autosuggestion library...
    "dal_select2",  # select 2 implementation for the front-end
    # "ckeditor",
    # internal applications
    "apps.users",
    "tabular_permissions",
    "fontawesomefree",
    "django_flatpickr",
    "apps.organization",
    # "apps.dashboard",
    # "apps.ecommerce",
    "apps.orders",
    # "apps.transfers",
    # "apps.cashflow",
    # "ckeditor",
    # "apps.coverages",
    # "apps.boxes",
    # "apps.websites",
    # "apps.invitations",
    # "apps.notifications",
    "apps.subscriptions",
    "apps.reports",
    # "apps.attendances",
    # "apps.iot",
    "apps.core",
    "template_partials",
    # "apps.services",
    # "apps.pendingfacturations",
    # admin app must be the last app (order matters!)
    "django.contrib.admin",
]

# Since using a UUIDField for the history_id
# is a common use case, there is a
# SIMPLE_HISTORY_HISTORY_ID_USE_UUID setting
# that will set all instances of history_id to UUIDs.
# SIMPLE_HISTORY_HISTORY_ID_USE_UUID = True
# Always use notebook for shell_plus
SHELL_PLUS = "notebook"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.environ["CLOUDINARY_CLOUD_NAME"],
    "API_KEY": os.environ["CLOUDINARY_API_KEY"],
    "API_SECRET": os.environ["CLOUDINARY_API_SECRET"],
}

# users model
AUTH_USER_MODEL = "users.User"
# users authentication urls

SITE_ID = 1  # declare the site id variable here
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_ADAPTER = "apps.users.adapters.SignUpAccountAdapter"
ACCOUNT_SIGNUP_REDIRECT_URL = "users:register_done"
LOGIN_REDIRECT_URL = "users:accounts"
LOGIN_URL = "account_login"
LOGOUT_URL = "/"

# Control the forms that django-allauth uses
ACCOUNT_FORMS = {
    "login": "allauth.account.forms.LoginForm",
    "add_email": "allauth.account.forms.AddEmailForm",
    "change_password": "allauth.account.forms.ChangePasswordForm",
    "set_password": "allauth.account.forms.SetPasswordForm",
    "reset_password": "allauth.account.forms.ResetPasswordForm",
    "reset_password_from_key": "allauth.account.forms.ResetPasswordKeyForm",
    "disconnect": "allauth.socialaccount.forms.DisconnectForm",
    # Use our custom signup form
    "signup": "apps.users.forms.UserRegistrationForm",
}

# settings.py


DATE_INPUT_FORMATS = [
    "%Y-%m-%d",  # Example: 2025-01-18 (default ISO format)
    "%m/%d/%Y",  # Example: 01/18/2025 (US format)
    "%d/%m/%Y",  # Example: 18/01/2025
]

# django crispy forms settings
CRISPY_ALLOWED_TEMPLATE_PACKS = ("bulma",)

CRISPY_TEMPLATE_PACK = "bulma"

# organization auto slug field support
ORGS_SLUGFIELD = "django_extensions.db.fields.AutoSlugField"

# For the toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]

MIDDLEWARE = [
    # "django_hosts.middleware.HostsRequestMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # Add whitenoise for serving static assets in production
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Add the account middleware:
    "allauth.account.middleware.AccountMiddleware",
    # "simple_history.middleware.HistoryRequestMiddleware",
    # Add django_htmx for attaching htmx attribute to each request
    "django_htmx.middleware.HtmxMiddleware",
    # Add organization for attaching organization attribute to each request
    # "django_hosts.middleware.HostsResponseMiddleware",
    "apps.organization.middleware.TimezoneMiddleware",
    # "apps.users.middleware.UserTimezoneMiddleware",
    "apps.organization.middleware.OrganizationMiddleware",
]

# SESSION_COOKIE_DOMAIN = ".distrivite.local"
# PARENT_HOST = "distrivite.local:8000"
# ROOT_HOSTCONF = "distrivite.hosts"
ROOT_URLCONF = "distrivite.urls"
# DEFAULT_HOST = "www"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.organization.context_processors.auth",
                "apps.subscriptions.context_processors.subscription",
                # "apps.orders.context_processors.basket",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by email
    "allauth.account.auth_backends.AuthenticationBackend",
]

WSGI_APPLICATION = "distrivite.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"
# TIME_ZONE = "UTC"
TIME_ZONE = "Africa/Douala"
USE_TZ = True
USE_I18N = True

# Set the default file system encoding to utf-8
if sys.version_info.major == 3:
    import locale

    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email settings for opticio
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = "liedjiwenkack@gmail.com"
EMAIL_HOST_PASSWORD = (
    "zneb bkbn qfsz dcmu"  # liedjiwenkack@gmail.com password for opticio account
)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
# IOT SETTINGS WITH MQTT CLIENT
MQTT_SERVER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_USER = ""
MQTT_PASSWORD = ""

# django restframewok settings

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 30,
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("JWT",),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=600),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}


DJOSER = {
    "SERIALIZERS": {
        "user_create": "apps.users.serializers.UserSerializer",
        "user": "apps.users.serializers.UserSerializer",
    },
}

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")
