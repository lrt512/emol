import os

from emol.secrets import get_secret

from .defaults import *  # noqa: F401, F403

AWS_REGION = "ca-central-1"

BASE_URL = "http://localhost:8000"
SECRET_KEY = "super-secret-test-key-1234"

DEBUG = True
NO_ENFORCE_PERMISSIONS = True
ALLOWED_HOSTS = ["localhost"]

# Configure Google authentication
AUTHLIB_OAUTH_CLIENTS = {
    "google": {
        "client_id": "..fake..",
        "client_secret": "..fake..",
    }
}

TIME_ZONE = "America/Toronto"

# email stuff
SEND_EMAIL = False
MAIL_DEFAULT_SENDER = "kingdom.emol@gmail.com"

# Kingdom stuff
MOL_EMAIL = "kingdom.mol@gmail.com"

# Reminders app config
REMINDER_DAYS = [60, 30, 14, 0]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "test.sqlite3"),
    },
    "cache_db": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "test_cache.sqlite3"),
    },
}

# Security config
CORS_ORIGIN_WHITELIST = [
    "http://localhost",
]

# Mock OAuth user configuration for development/testing
MOCK_OAUTH_USER = {
    "is_superuser": True,
    "is_staff": True,
}
