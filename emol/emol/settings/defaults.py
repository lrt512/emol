from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = False
NO_ENFORCE_PERMISSIONS = False

SECURE_HSTS_SECONDS = 31536000

INSTALLED_APPS = [
    "sso_user",  # needs to be before contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "feature_switches",
    "cards",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "global_throttle.middleware.GlobalThrottleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "current_user.middleware.ThreadLocalUserMiddleware",
]

ROOT_URLCONF = "emol.urls"
STATIC_URL = "static/"
STATIC_ROOT = "/opt/emol/static/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates/"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "emol.wsgi.application"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "app",
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "/var/log/emol/emol.log",
            "when": "D",
            "interval": 1,
            "backupCount": 7,
            "formatter": "app",
            "encoding": "utf-8",
        },
    },
    "root": {"level": "INFO", "handlers": ["console", "file"]},
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "cards": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
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
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
        "global_throttle": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "formatters": {
        "app": {
            "format": "%(asctime)s [%(levelname)-8s] %(name)s "
            "(%(module)s.%(funcName)s:%(lineno)d) %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
}


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "emol_cache",
    }
}

CACHE_TTL = 60 * 15  # 15 minutes
LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication config
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_USER_MODEL = "sso_user.SSOUser"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ]
}

# email stuff
SEND_EMAIL = True

# Security config
CORS_ORIGIN_WHITELIST = [
    "http://localhost",
]

SECURE_HSTS_SECONDS = 31536000
PERMISSIONS_POLICY = {
    "accelerometer": [],
    "autoplay": [],
    "camera": [],
    "display-capture": [],
    "encrypted-media": [],
    "fullscreen": [],
    "geolocation": [],
    "gyroscope": [],
    "magnetometer": [],
    "microphone": [],
    "midi": [],
    "payment": [],
    "usb": [],
}

CSP_IMG_SRC = ("'self'", "data:", "https://cdn.datatables.net")
CSP_FONT_SRC = (
    "'self'",
    "https://maxcdn.bootstrapcdn.com",
    "https://cdnjs.cloudflare.com",
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # needed for datatables
    "https://cdnjs.cloudflare.com",
    "https://maxcdn.bootstrapcdn.com",
    "https://cdn.datatables.net",
)
CSP_SCRIPT_SRC = (
    "'self'",
    "https://cdnjs.cloudflare.com",
    "https://maxcdn.bootstrapcdn.com",
    "https://cdn.datatables.net",
    "sha256-PhCsD9cDmNHcYlaLal8yHa4TGyayjyPy1/u4cyvSojQ=",
)

# Reminder configuration
REMINDER_DAYS = [60, 30, 14, 0]
