"""Production settings for eMoL."""

from typing import Any, cast

from emol.secrets import get_secret

from .defaults import *  # noqa: F403, F401

AWS_REGION = "ca-central-1"

SECRET_KEY = get_secret("/emol/secret_key")
BASE_URL = "https://emol.ealdormere.ca"

# Security settings for production
DEBUG = False
ALLOWED_HOSTS = ["emol.ealdormere.ca", "localhost", "127.0.0.1", "testserver"]

# SSL/HTTPS settings
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = False  # Allow HTTP for internal testing (behind proxy)
CSRF_COOKIE_SECURE = False  # Allow HTTP for internal testing

TIME_ZONE = "America/Toronto"

# Email configuration
SEND_EMAIL = True
MAIL_DEFAULT_SENDER = "ealdormere.emol@gmail.com"
MOL_EMAIL = "ealdormere.mol@gmail.com"
EMAILER = "emol.emailer.AWSEmailer"

# OAuth configuration
OAUTH_CLIENT_ID = get_secret("/emol/oauth_client_id")
OAUTH_CLIENT_SECRET = get_secret("/emol/oauth_client_secret")

AUTHLIB_OAUTH_CLIENTS = {
    "google": {
        "client_id": get_secret("/emol/oauth_client_id"),
        "client_secret": get_secret("/emol/oauth_client_secret"),
    }
}

# Production database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": get_secret("/emol/db_name"),
        "USER": get_secret("/emol/db_user"),
        "PASSWORD": get_secret("/emol/db_password"),
        "HOST": get_secret("/emol/db_host"),
        "PORT": "3306",
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
    }
}

# Reminder configuration
REMINDER_DAYS = [60, 30, 14, 0]

# Throttling configuration
GLOBAL_THROTTLE_LIMIT = 1000
GLOBAL_THROTTLE_WINDOW = 3600

# Production logging goes to files
LOGGING["handlers"]["file"]["filename"] = "/var/log/emol/emol.log"  # type: ignore[index]  # noqa: F405 E501

# Static files in production
STATIC_ROOT = "/opt/emol/static/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Cache configuration for production
CACHES["default"] = cast(  # type: ignore[index]  # noqa: F405
    dict[str, Any],
    {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "emol_cache",
        "TIMEOUT": 300,
        "OPTIONS": {
            "MAX_ENTRIES": 10000,
        },
    },
)

# Production performance settings
USE_TZ = True
