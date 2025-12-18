from emol.secrets import get_secret
from emol.settings.defaults import *  # noqa: F401, F403

AWS_REGION = "ca-central-1"

BASE_URL = "http://localhost:8000"
SECRET_KEY = "super-secret-development-key-1234"

DEBUG = True
NO_ENFORCE_PERMISSIONS = True
ALLOWED_HOSTS = ["localhost"]

# Override CSP settings for development to allow inline scripts (for debugging)
CSP_SCRIPT_SRC = (  # type: ignore[no-redef]
    "'self'",
    "https://cdnjs.cloudflare.com",
    "https://maxcdn.bootstrapcdn.com",
    "https://cdn.datatables.net",
    "sha256-PhCsD9cDmNHcYlaLal8yHa4TGyayjyPy1/u4cyvSojQ=",
    "'unsafe-inline'",  # Temporarily allow inline scripts
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "[{levelname}] {asctime} {name} {lineno}: {message}",
            "style": "{",
        },
        "file": {
            "format": "{levelname} {asctime} {name} {lineno} {process:d} {thread:d} {message}",  # noqa: E501
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "console",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "/var/log/emol/django.log",
            "formatter": "file",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "global_throttle": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "cards": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "sso_user": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

AUTHLIB_OAUTH_CLIENTS = {
    "google": {
        "client_id": "mock-client-id",
        "client_secret": "mock-client-secret",
    }
}
TIME_ZONE = "America/Toronto"

# email stuff
SEND_EMAIL = False
MAIL_DEFAULT_SENDER = "ealdormere.emol@gmail.com"

# Kingdom stuff
MOL_EMAIL = "ealdormere.mol@gmail.com"

# Reminders app config
REMINDER_DAYS = [60, 30, 14, 0]

# Global throttle config
GLOBAL_THROTTLE_LIMIT = 20000
GLOBAL_THROTTLE_WINDOW = 3600

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": get_secret("/emol/db_host"),
        "NAME": get_secret("/emol/db_name"),
        "USER": get_secret("/emol/db_user"),
        "PASSWORD": get_secret("/emol/db_password"),
    },
    "cache_db": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": get_secret("/emol/db_host"),
        "NAME": f"{get_secret('/emol/db_name')}_cache",
        "USER": get_secret("/emol/db_user"),
        "PASSWORD": get_secret("/emol/db_password"),
    },
}

# Security config
CORS_ORIGIN_WHITELIST = [
    "http://localhost",
]

# Mock OAuth settings for development
MOCK_OAUTH_USER = {
    "email": "dev@example.com",
    "name": "Development User",
    "is_superuser": True,  # Make the dev user a superuser by default
    "is_staff": True,
}
