# Development Settings Template

This is a template for creating development settings. The actual development settings are in `emol/emol/settings/dev.py`, but this serves as a reference.

## Sample Development Settings

**Base Configuration:**
```python
AWS_REGION = "ca-central-1"
BASE_URL = "http://localhost:8000"
SECRET_KEY = "super-secret-development-key-1234"
DEBUG = True
NO_ENFORCE_PERMISSIONS = True
ALLOWED_HOSTS = ["localhost"]
```

**OAuth Configuration:**
```python
AUTHLIB_OAUTH_CLIENTS = {
    "google": {
        "client_id": get_secret("/emol/oauth_client_id"),
        "client_secret": get_secret("/emol/oauth_client_secret"),
    }
}
```

**Email Settings:**
```python
SEND_EMAIL = False
MAIL_DEFAULT_SENDER = "emol@kingdom.org"
MOL_EMAIL = "minister.of.lists@kingdom.org"
```

**Database Configuration (for Docker Compose):**
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": os.environ.get("DB_HOST"),
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
    },
    "cache_db": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": os.environ.get("DB_HOST"),
        "NAME": f"{os.environ.get('DB_NAME')}_cache",
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
    },
}
```

**Throttling:**
```python
GLOBAL_THROTTLE_LIMIT = 20000
GLOBAL_THROTTLE_WINDOW = 3600
```

## Note

The actual development settings file is `emol/emol/settings/dev.py` and is already configured for the Docker-based development environment. You typically do not need to modify it unless you have specific local requirements.
