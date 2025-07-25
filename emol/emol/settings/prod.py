"""Production settings for eMoL."""

from .defaults import *  # noqa: F403, F401
from emol.secrets import get_secret

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
            "sql_mode": "STRICT_TRANS_TABLES",
        },
    }
}

# Security settings for production
DEBUG = False
ALLOWED_HOSTS = ["emol.ealdormere.ca", "localhost", "127.0.0.1"]

# SSL/HTTPS settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# OAuth configuration
OAUTH_CLIENT_ID = get_secret("/emol/oauth_client_id")
OAUTH_CLIENT_SECRET = get_secret("/emol/oauth_client_secret")

# Email configuration (production)
SEND_EMAIL = True

# Throttling configuration - DISABLED
GLOBAL_THROTTLE_LIMIT = 1000000  # Effectively disabled
GLOBAL_THROTTLE_WINDOW = 3600

# Production logging goes to files
LOGGING["handlers"]["file"]["filename"] = "/var/log/emol/emol.log"  # noqa: F405

# Static files in production
STATIC_ROOT = "/opt/emol/static/"

# Cache configuration for production
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "emol_cache",
        "TIMEOUT": 300,
        "OPTIONS": {
            "MAX_ENTRIES": 10000,
        }
    }
}

# Production performance settings
USE_TZ = True 