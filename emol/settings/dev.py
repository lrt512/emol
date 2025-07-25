print("Loading dev.py settings...")
import os

from emol.secrets import get_secret

from .defaults import *  # noqa: F401, F403

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO", # Or "DEBUG" for more detailed logs in development
        },
        "emol": { # Or your app's name if different from 'emol'
            "handlers": ["console"],
            "level": "DEBUG", # Set to DEBUG for your application logs
        },
    },
}

LOGIN_REDIRECT_URL = '/auth/accounts/profile/'

# ... rest of your settings ... 