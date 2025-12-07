# Production Settings Template

This is a template for creating production settings. Use this as a reference when creating `/opt/emol_config/emol_production.py` on your production server.

## Base Settings for Production Deployment

### Required Configuration

**AWS Region:**
```python
AWS_REGION = "ca-central-1"
```

**Secret Key:**
```python
SECRET_KEY = get_secret("/emol/secret_key")
```

**Base URL:**
```python
BASE_URL = "http://yourdomain.com"
```

**Allowed Hosts:**
```python
ALLOWED_HOSTS = ["yourdomain.com"]
```

### Optional Configuration

**Timezone:**
```python
TIME_ZONE = "America/Toronto"
```

**Email Settings:**
```python
MAIL_DEFAULT_SENDER = "emol@kingdom.org"
MOL_EMAIL = "minister.of.lists@kingdom.org"
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

**Database Configuration:**
```python
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
```

**Reminder Configuration:**
```python
REMINDER_DAYS = [60, 30, 14, 0]
```

**Throttling Configuration:**
```python
GLOBAL_THROTTLE_LIMIT = 20
GLOBAL_THROTTLE_WINDOW = 3600
```

## Creating Instance-Specific Overrides

To override production settings for a specific instance, create `/opt/emol_config/emol_production.py`:

```python
from emol.settings.prod import *

# Override only what you need
ALLOWED_HOSTS = ["your-domain.com"]
BASE_URL = "https://your-domain.com"
```

This file will be automatically loaded by `emol.settings.prod` if it exists.
